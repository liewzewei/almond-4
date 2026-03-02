import logging
from ultralytics import YOLO
import torch

class Tracker:
    def __init__(self, model_name="yolov8n.pt", tracker_config="bytetrack.yaml", conf_threshold=0.4):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = YOLO(model_name)
        self.tracker_config = tracker_config
        self.conf_threshold = conf_threshold
        self.target_classes = [2, 3, 5, 7]
        
        logging.info(f"Tracker initialized on {self.device} using {tracker_config}")

    def track(self, frame, imgsz=640):
        # Use YOLOv8 built-in track() which handles detection + tracking
        results = self.model.track(
            source=frame,
            persist=True,
            tracker=self.tracker_config,
            conf=self.conf_threshold,
            classes=self.target_classes,
            device=self.device,
            imgsz=imgsz,
            half=(self.device == 'cuda'),
            verbose=False
        )
        
        tracks = []
        if results and len(results) > 0:
            boxes = results[0].boxes
            if boxes.id is not None:
                ids = boxes.id.cpu().numpy().astype(int)
                bboxes = boxes.xyxy.cpu().numpy()
                confs = boxes.conf.cpu().numpy()
                classes = boxes.cls.cpu().numpy().astype(int)
                
                for i in range(len(ids)):
                    tracks.append({
                        "track_id": ids[i],
                        "bbox": bboxes[i].tolist(),
                        "conf": float(confs[i]),
                        "class_id": classes[i]
                    })
                    
        return tracks
