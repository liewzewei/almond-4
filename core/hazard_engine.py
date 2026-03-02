import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

class HazardEngine:
    def __init__(self, weights: Dict[str, float], threshold=2.0, smoothing_frames=12):
        self.weights = weights
        self.threshold = threshold
        self.smoothing_frames = smoothing_frames
        
        # Baseline stats for normalization (computed during warm-up)
        self.baselines: Dict[str, float] = {}
        self.warmup_data: Dict[str, List[float]] = {k: [] for k in weights.keys()}
        self.is_warmed_up = False
        
        # Temporal smoothing: track_id -> list of recent hazard scores
        self.score_history: Dict[int, List[float]] = {}

    def update_warmup(self, features: Dict[str, float]):
        for k, v in features.items():
            if k in self.warmup_data:
                self.warmup_data[k].append(v)

    def finalize_warmup(self):
        for k, values in self.warmup_data.items():
            if values:
                # Use Median Absolute Deviation or just mean/std
                self.baselines[k] = np.std(values) if np.std(values) > 0 else 1.0
        self.is_warmed_up = True
        logging.info(f"Hazard engine warm-up complete. Baselines: {self.baselines}")

    def compute_hazard_score(self, track_id: int, features: Dict[str, float]) -> Tuple[float, bool]:
        if not self.is_warmed_up:
            return 0.0, False
            
        # Normalize and weight
        local_scores = []
        for k, w in self.weights.items():
            val = features.get(k, 0.0)
            baseline = self.baselines.get(k, 1.0)
            norm_val = val / baseline
            local_scores.append(norm_val * w)
            
        current_hazard = sum(local_scores)
        
        # Temporal smoothing
        if track_id not in self.score_history:
            self.score_history[track_id] = []
            
        self.score_history[track_id].append(current_hazard)
        if len(self.score_history[track_id]) > self.smoothing_frames:
            self.score_history[track_id].pop(0)
            
        # Check if consistently above threshold
        avg_hazard = np.mean(self.score_history[track_id])
        is_hazard = avg_hazard > self.threshold and len(self.score_history[track_id]) >= self.smoothing_frames
        
        return avg_hazard, is_hazard
