import numpy as np
import logging
from collections import deque
from typing import Dict, List

class OnlineRobustBaseline:
    """
    Maintains a robust baseline of "normal" vehicle behavior using 
    Median Absolute Deviation (MAD).
    """
    def __init__(self, max_samples=500, min_samples=30, sigma_floor=1e-3):
        self.max_samples = max_samples
        self.min_samples = min_samples
        self.sigma_floor = sigma_floor
        
        # Buffers for each feature: feature_name -> deque
        self.buffers: Dict[str, deque] = {}
        
        # Cached values
        self.medians: Dict[str, float] = {}
        self.sigmas: Dict[str, float] = {}
        
    def update(self, feature_dict: Dict[str, float], current_risk: float):
        """
        Updates the baseline if the vehicle is considered "normal" (risk < 0.6).
        """
        if current_risk >= 0.6:
            return
            
        for name, value in feature_dict.items():
            if name not in self.buffers:
                self.buffers[name] = deque(maxlen=self.max_samples)
            
            self.buffers[name].append(value)
            
            # Periodically recompute (e.g., every 5 samples once minimal reached)
            if len(self.buffers[name]) >= self.min_samples and len(self.buffers[name]) % 5 == 0:
                self._recompute_feature(name)
                
    def _recompute_feature(self, name: str):
        data = np.array(self.buffers[name])
        median = np.median(data)
        
        # Median Absolute Deviation
        mad = np.median(np.abs(data - median))
        
        # Consistency constant for normal distribution: 1.4826
        sigma = 1.4826 * mad
        sigma = max(sigma, self.sigma_floor)
        
        self.medians[name] = median
        self.sigmas[name] = sigma
        
    def get_median(self, feature_name: str) -> float:
        return self.medians.get(feature_name, 0.0)
        
    def get_sigma(self, feature_name: str) -> float:
        return self.sigmas.get(feature_name, 1.0) # Default to 1.0 to avoid div by zero if not enough samples
        
    def is_ready(self, feature_name: str) -> bool:
        return len(self.buffers.get(feature_name, [])) >= self.min_samples
