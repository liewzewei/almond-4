import argparse
import yaml
import logging
import time
import pandas as pd
from tqdm import tqdm
from core.video_processor import VideoProcessor
from core.tracker import Tracker
from core.engine import RiskEngine
from core.alert_writer import AlertWriter

def setup_logging(log_path):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ],
        force=True
    )

def run_pipeline(config, video_path, dry_run_frames=None):
    # Initialize components
    vp = VideoProcessor(video_path)
    tracker = Tracker(config['yolo_model'], config['tracker_type'], config['yolo_conf_threshold'])
    
    # Use the new RiskEngine
    config['fps'] = vp.fps
    engine = RiskEngine(config)
    
    aw = AlertWriter(config['alert_queue_path'], config['camera_id'])
    
    setup_logging(config['pipeline_log_path'])
    logging.info(f"Starting generalized pipeline on {video_path}")
    
    frame_idx = 0
    start_time = time.time()
    tracks_data = []
    
    pbar = tqdm(total=dry_run_frames if (dry_run_frames and vp.total_frames > 0) else (vp.total_frames if vp.total_frames > 0 else None))
    
    try:
        while True:
            if dry_run_frames and frame_idx >= dry_run_frames:
                break
                
            raw_frame = vp.get_frame()
            if raw_frame is None:
                break
                
            timestamp = frame_idx / vp.fps
            
            # 1. Track
            # imgsz = config.get('imgsz', 640)
            tracks = tracker.track(raw_frame)
            
            # 2. Process through RiskEngine
            results = engine.process_frame(raw_frame, tracks, frame_idx, timestamp)
            
            # 3. Handle Alerts and Logging
            for res in results:
                tid = res['track_id']
                risk_score = res['risk_score']
                features = res['features']
                
                # Log track features for evaluation
                feat_log = {"frame": frame_idx, "track_id": tid, "risk": risk_score, **features}
                tracks_data.append(feat_log)
                
                if res['is_alert']:
                    aw.write_alert(tid, frame_idx, risk_score, features, res['bbox'], raw_frame)
            
            frame_idx += 1
            pbar.update(1)
            
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
    finally:
        vp.release()
        pbar.close()
        
        # Save tracks log for evaluation
        if tracks_data:
            df = pd.DataFrame(tracks_data)
            df.to_csv(config['tracks_log_path'], index=False)
            logging.info(f"Saved evaluation logs to {config['tracks_log_path']}")
            
        end_time = time.time()
        elapsed = end_time - start_time
        fps = frame_idx / elapsed if elapsed > 0 else 0
        logging.info(f"Processing finished. Total frames: {frame_idx}, Avg FPS: {fps:.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Highway Hazard Detection CLI")
    parser.add_argument("--video", type=str, required=True, help="Path to input video")
    parser.add_argument("--mode", type=str, choices=["run", "dryrun"], default="run")
    parser.add_argument("--frames", type=int, default=0, help="Number of frames for dryrun")
    args = parser.parse_args()
    
    with open("config.yaml", 'r') as f:
        config = yaml.safe_load(f)
        
    config['target_size'] = [config['target_width'], config['target_height']]
        
    run_pipeline(config, args.video, args.frames if args.mode == "dryrun" else None)
