import os
import cv2
import uuid
import base64
import json
import time
from flask import Blueprint, Response, jsonify, request, current_app, render_template
from werkzeug.utils import secure_filename

api_bp = Blueprint('api', __name__)

def generate_frames(worker):
    while True:
        with worker.lock:
            frame = worker.latest_frame
            if frame is None:
                continue
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@api_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html', cam_id=1)

@api_bp.route('/camera/<int:cam_id>', methods=['GET'])
def camera_view(cam_id):
    return render_template('index.html', cam_id=cam_id)

@api_bp.route('/camera/<int:cam_id>/stream', methods=['GET'])
def video_feed(cam_id):
    # This assumes the app context has access to the worker
    worker = current_app.camera_worker
    return Response(generate_frames(worker),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@api_bp.route('/camera/<int:cam_id>/status', methods=['GET'])
def camera_status(cam_id):
    worker = current_app.camera_worker
    with worker.lock:
        return jsonify({
            "mode": worker.mode,
            "processing": worker.processing,
            "risk_score": worker.latest_risk,
            "alert_count": len(worker.alerts),
            "alerts": worker.alerts[-20:] if worker.alerts else []
        })

@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    worker = current_app.camera_worker
    with worker.lock:
        return jsonify(worker.alerts)

@api_bp.route('/camera/<int:cam_id>/upload', methods=['POST'])
def upload_video(cam_id):
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(current_app.config_obj.UPLOADS_DIR, filename)
        file.save(save_path)
        
        worker = current_app.camera_worker
        worker.set_source(save_path, mode="file")
        
        return jsonify({"success": True, "path": save_path})

@api_bp.route('/camera/<int:cam_id>/switch/live', methods=['POST'])
def switch_to_live(cam_id):
    worker = current_app.camera_worker
    worker.set_source(0, mode="live")
    return jsonify({"success": True, "mode": "live"})

# --- New endpoints for React Frontend Integration ---

@api_bp.route('/upload', methods=['POST'])
def react_upload_video():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        video_id = str(uuid.uuid4())
        # Use existing uploads dir
        ext = os.path.splitext(file.filename)[1]
        save_path = os.path.join(current_app.config_obj.UPLOADS_DIR, f"{video_id}{ext}")
        file.save(save_path)
        
        return jsonify({"video_id": video_id, "file_path": save_path})

@api_bp.route('/process/<video_id>', methods=['GET'])
def react_process_video(video_id):
    # Find the file
    target_path = None
    for ext in ['.mp4', '.mov', '.avi']:
        p = os.path.join(current_app.config_obj.UPLOADS_DIR, f"{video_id}{ext}")
        if os.path.exists(p):
            target_path = p
            break
            
    if not target_path:
        return jsonify({"error": "Video not found"}), 404

    def sse_generator():
        from core.video_processor import VideoProcessor
        from core.tracker import Tracker
        from core.engine import RiskEngine
        
        cfg = current_app.config_obj.__dict__.copy()
        vp = None
        try:
            # We recreate a minimal pipeline for this single video stream
            vp = VideoProcessor(target_path, (cfg.get('TARGET_WIDTH', 1280), cfg.get('TARGET_HEIGHT', 720)))
            tracker = Tracker(cfg.get('YOLO_MODEL', 'yolov8n.pt'), cfg.get('TRACKER_TYPE', 'bytetrack.yaml'), cfg.get('CONF_THRESHOLD', 0.25))
            
            # Pack dict for RiskEngine
            engine_cfg = current_app.config_obj.raw_config.copy()
            engine_cfg['fps'] = vp.fps
            engine = RiskEngine(engine_cfg)
            
            frame_idx = 0
            while True:
                orig_frame, processed_frame = vp.get_frame()
                if processed_frame is None:
                    break
                    
                timestamp = frame_idx / vp.fps
                tracks = tracker.track(processed_frame)
                results = engine.process_frame(processed_frame, tracks, frame_idx, timestamp)
                
                # Draw annotations (simplified)
                annotated = processed_frame.copy()
                for res in results:
                    tid = res['track_id']
                    bbox = res['bbox']
                    risk = res['risk_score']
                    color = (0, 0, 255) if res.get('is_alert') else (0, 255, 0)
                    x1, y1, x2, y2 = map(int, bbox)
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                
                # Encode to base64 for SSE
                ret, buffer = cv2.imencode('.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                if ret:
                    b64_img = base64.b64encode(buffer).decode('utf-8')
                    yield f"data: {json.dumps({'status': 'processing', 'annotated_frame': b64_img})}\n\n"
                    
                frame_idx += 1
                time.sleep(0.01) # Small sleep to yield
                
            yield f"data: {json.dumps({'status': 'completed'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
        finally:
            if vp:
                vp.release()

    return Response(sse_generator(), mimetype='text/event-stream')
