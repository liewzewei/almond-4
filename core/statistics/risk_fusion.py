import numpy as np
import logging
from typing import Dict, List

class RiskFusionEngine:
    """
    Combines independent feature probabilities into a single risk score
    using Noisy-OR logic and temporal smoothing.
    """
    def __init__(self, weights: Dict[str, float] = None, alpha=0.4):
        # Default weights if not provided
        self.weights = weights or {
            'sdlp': 0.25,
            'steering_entropy': 0.25,
            'lateral_band_energy': 0.20,
            'speed_cv': 0.20,
            'jerk_rms': 0.10
        }
        self.alpha = alpha
        
        # State: track_id -> smoothed_risk
        self.history: Dict[int, float] = {}
        # Multi-frame alert tracker: track_id -> count of frames above alert threshold
        self.alert_counts: Dict[int, int] = {}
        
    def fuse(self, track_id: int, probabilities: Dict[str, float], fps: float) -> float:
        """
        Computes the fused risk score for a single track.
        """
        # 1. Noisy-OR Fusion
        # R_raw = 1 - product(1 - w_i * A_i)
        prod_term = 1.0
        for feat, prob in probabilities.items():
            weight = self.weights.get(feat, 0.1)
            prod_term *= (1.0 - weight * prob)
            
        r_raw = 1.0 - prod_term
        
        # 2. Exponential Smoothing
        prev_r = self.history.get(track_id, r_raw)
        r_smoothed = self.alpha * r_raw + (1.0 - self.alpha) * prev_r
        
        self.history[track_id] = r_smoothed
        return float(np.clip(r_smoothed, 0, 1))
        
    def check_alert(self, track_id: int, risk: float, fps: float) -> bool:
        """
        Alert rule: R_t > 0.85 sustained for >= 1.5 sec.
        """
        threshold = 0.85
        required_frames = int(1.5 * fps)
        
        if risk > threshold:
            self.alert_counts[track_id] = self.alert_counts.get(track_id, 0) + 1
        else:
            self.alert_counts[track_id] = 0
            
        return self.alert_counts[track_id] >= required_frames
        
    def cleanup(self, active_ids: List[int]):
        """
        Removes history for non-active tracks.
        """
        current_ids = list(self.history.keys())
        for tid in current_ids:
            if tid not in active_ids:
                if tid in self.history: del self.history[tid]
                if tid in self.alert_counts: del self.alert_counts[tid]
