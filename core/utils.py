import cv2
import numpy as np
import json
import os
from typing import Tuple, List

def get_bbox_center_bottom(bbox: List[float]) -> Tuple[float, float]:
    """Returns the bottom-center coordinate of a bbox [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) / 2
    cy = y2
    return cx, cy

def calculate_iou(boxA, boxB):
    """Calculates Intersection over Union of two bounding boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

def draw_info(frame, text, pos):
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

class AlertEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (np.integer, np.int32, np.int64)):
            return int(o)
        if isinstance(o, (np.floating, np.float32, np.float64)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return super().default(o)
