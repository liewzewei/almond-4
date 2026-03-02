from collections import deque
import time
from typing import Dict, List, Tuple
from core.utils import get_bbox_center_bottom

class TrajectoryManager:
    def __init__(self, max_points=150):
        self.trajectories: Dict[int, deque] = {}
        self.max_points = max_points
        self.last_seen: Dict[int, float] = {}

    def update(self, tracks: List[dict], frame_idx: int, timestamp: float, bev_transformer=None, h_matrix=None):
        active_ids = []
        for track in tracks:
            tid = track["track_id"]
            bbox = track["bbox"]
            cx, cy = get_bbox_center_bottom(bbox)
            
            # Apply BEV transformation if available
            if bev_transformer and h_matrix is not None:
                bev_pt = bev_transformer.transform_point([cx, cy], h_matrix)
                bev_x, bev_y = bev_pt
            else:
                bev_x, bev_y = cx, cy
            
            if tid not in self.trajectories:
                self.trajectories[tid] = deque(maxlen=self.max_points)
                
            self.trajectories[tid].append({
                "frame_idx": frame_idx,
                "timestamp": timestamp,
                "cx": cx,
                "cy": cy,
                "bev_x": bev_x,
                "bev_y": bev_y,
                "bbox": bbox,
                "class_id": track["class_id"]
            })
            self.last_seen[tid] = timestamp
            active_ids.append(tid)
            
        # Optional: cleanup very old tracks
        self._cleanup(timestamp)
        return active_ids

    def get_trajectory(self, track_id: int) -> List[dict]:
        return list(self.trajectories.get(track_id, []))

    def _cleanup(self, current_time: float, max_age=30.0):
        to_delete = [tid for tid, last_t in self.last_seen.items() 
                     if current_time - last_t > max_age]
        for tid in to_delete:
            del self.trajectories[tid]
            del self.last_seen[tid]
