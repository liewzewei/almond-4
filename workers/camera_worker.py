import cv2
import threading
import time
import logging
import os
import numpy as np
from core.engine import RiskEngine
from core.tracker import Tracker
from core.alert_writer import AlertWriter

class CameraWorker(threading.Thread):
    def __init__(self, camera_id=1, source=0, config_obj=None):
        super().__init__()
        self.daemon = True
        self.config = config_obj
        self.camera_id = camera_id
        self.current_source = source
        self.mode = "live" if isinstance(source, int) else "file"
        
        self.cap = None
        self.latest_frame = None
        self.latest_risk = 0.0
        self.alerts = []
        self.processing = False
        self.running = False
        self.fps = 30.0
        
        # Thread safety
        self.lock = threading.Lock()
        
        # AI Components (Global config passed to RiskEngine)
        self.tracker = None
        self.engine = None
        self.alert_writer = None
        
        logging.info(f"CameraWorker {camera_id} initialized for source {source}")

    def _initialize_ai(self):
        """Lazy initialization of AI components inside the thread."""
        if self.tracker is None:
            self.tracker = Tracker(
                model_name=self.config.YOLO_MODEL,
                tracker_config=self.config.TRACKER_TYPE,
                conf_threshold=self.config.CONF_THRESHOLD
            )
        if self.engine is None:
            # We need to provide a dict config to RiskEngine
            engine_cfg = self.config.raw_config.copy()
            engine_cfg['fps'] = self.fps
            self.engine = RiskEngine(engine_cfg)
        
        if self.alert_writer is None:
            self.alert_writer = AlertWriter(
                self.config.get('alert_queue_path', 'tmp/alerts_queue.json'),
                f"CAM_{self.camera_id}"
            )

    def set_source(self, source, mode="live"):
        with self.lock:
            self.current_source = source
            self.mode = mode
            self.processing = True
            if self.cap:
                self.cap.release()
            self.cap = cv2.VideoCapture(source)
            if self.cap.is_opened():
                self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
                # Reset engine to handle new FPS or coordinate space if needed
                self.engine = None 
            logging.info(f"Source changed to {source} (Mode: {mode})")

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()

    def run(self):
        self.running = True
        self.processing = True
        
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.current_source)
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0

        self._initialize_ai()

        frame_idx = 0
        while self.running:
            if not self.processing:
                time.sleep(0.1)
                continue

            ret, frame = self.cap.read()
            if not ret:
                if self.mode == "file":
                    self.processing = False
                    logging.info("Video file ended.")
                else:
                    # Live camera retry
                    time.sleep(1)
                    self.cap.open(self.current_source)
                continue

            timestamp = frame_idx / self.fps
            
            # 1. AI Pipeline
            tracks = self.tracker.track(frame)
            results = self.engine.process_frame(frame, tracks, frame_idx, timestamp)
            
            # 2. Find max risk in current frame
            max_risk = 0.0
            if results:
                max_risk = max([r['risk_score'] for r in results])

            # 3. Annotation
            annotated = frame.copy()
            for res in results:
                x1, y1, x2, y2 = map(int, res['bbox'])
                tid = res['track_id']
                risk = res['risk_score']
                color = (0, 0, 255) if res['is_alert'] else (0, 255, 0)
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated, f"ID:{tid} R:{risk:.2f}", (x1, y1-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # 4. Handle Alerts (Snapshot Saving)
                if res['is_alert']:
                    alert_time = time.strftime("%Y%m%d-%H%M%S")
                    snap_name = f"alert_{self.camera_id}_{tid}_{alert_time}.jpg"
                    snap_path = os.path.join(self.config.SNAPSHOTS_DIR, snap_name)
                    cv2.imwrite(snap_path, frame) # Save raw frame for evidence
                    
                    alert_record = {
                        "track_id": tid,
                        "risk": risk,
                        "timestamp": timestamp,
                        "snapshot": snap_name,
                        "camera_id": self.camera_id
                    }
                    with self.lock:
                        self.alerts.append(alert_record)
                        if len(self.alerts) > 100: self.alerts.pop(0)

            # 5. Thread-safe updates
            with self.lock:
                self.latest_frame = annotated
                self.latest_risk = max_risk
            
            frame_idx += 1
            
            # Control processing speed for files
            if self.mode == "file":
                time.sleep(1.0 / self.fps)

        if self.cap:
            self.cap.release()
