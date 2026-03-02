import json
import os
import uuid
import cv2
import datetime
import logging
from typing import Dict, Any
from core.utils import AlertEncoder

class AlertWriter:
    def __init__(self, queue_path="tmp/alerts_queue.json", camera_id="CAM_LOCAL_01"):
        self.queue_path = queue_path
        self.camera_id = camera_id
        os.makedirs(os.path.dirname(queue_path), exist_ok=True)
        
        if not os.path.exists(queue_path):
            with open(queue_path, 'w') as f:
                json.dump([], f)

    def write_alert(self, track_id: int, frame_idx: int, risk_score: float, features: Dict[str, float], bbox: list, frame: Any):
        alert_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()
        
        # Save blurred thumbnail
        x1, y1, x2, y2 = map(int, bbox)
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        thumb = frame[y1:y2, x1:x2]
        if thumb.size > 0:
            # Heavily downsample and blur for privacy
            thumb = cv2.resize(thumb, (64, 64))
            thumb = cv2.GaussianBlur(thumb, (15, 15), 0)
            thumb_path = f"tmp/thumb_{alert_id}.jpg"
            cv2.imwrite(thumb_path, thumb)
        else:
            thumb_path = None

        alert = {
            "alert_id": alert_id,
            "timestamp_iso": timestamp,
            "camera_id": self.camera_id,
            "track_id": track_id,
            "frame_idx": frame_idx,
            "risk_score": risk_score,
            "features": features,
            "bbox": bbox,
            "thumbnail_path": thumb_path
        }
        
        # Append to queue
        try:
            with open(self.queue_path, 'r') as f:
                queue = json.load(f)
            queue.append(alert)
            with open(self.queue_path, 'w') as f:
                json.dump(queue, f, cls=AlertEncoder, indent=2)
            
            logging.info(f"ALERT TRIGGERED: Track {track_id} | Risk {risk_score:.2f}")
            return alert
        except Exception as e:
            logging.error(f"Failed to write alert: {e}")
            return None
