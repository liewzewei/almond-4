from ultralytics import YOLO
import torch
import logging

class Detector:
    def __init__(self, model_name="yolov8n.pt", conf_threshold=0.4):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = YOLO(model_name)
        self.conf_threshold = conf_threshold
        
        # COCO classes: car(2), motorcycle(3), bus(5), truck(7)
        self.target_classes = [2, 3, 5, 7]
        
        logging.info(f"Detector initialized on {self.device} with {model_name}")

    def detect(self, frame):
        # Run inference
        results = self.model.predict(
            source=frame,
            conf=self.conf_threshold,
            classes=self.target_classes,
            device=self.device,
            half=(self.device == 'cuda'),
            verbose=False
        )
        
        detections = []
        if results and len(results) > 0:
            boxes = results[0].boxes
            for box in boxes:
                detections.append({
                    "bbox": box.xyxy[0].tolist(), # [x1, y1, x2, y2]
                    "conf": float(box.conf[0]),
                    "class_id": int(box.cls[0])
                })
                
        return detections
