import numpy as np
from scipy.signal import savgol_filter
from scipy.fft import fft
from typing import List, Dict
import math
from .smoothing import smooth_trajectory

class FeatureEngine:
    """
    Computes research-grade motion features in BEV space.
    Inspired by driver impairment research (intoxication/fatigue).
    """
    def __init__(self, fps=30.0, window_sec=3.0):
        self.fps = fps
        self.window_size = int(window_sec * fps)
        
    def compute_features(self, trajectory: List[dict]) -> Dict[str, float]:
        """
        Main entry point for feature extraction from a trajectory.
        Trajectory is a list of dicts containing 'bev_x', 'bev_y', 'timestamp'.
        """
        if len(trajectory) < self.window_size // 2:
            return {}
            
        # 1. Extract and Smooth BEV Coordinates
        pts = np.array([[p['bev_x'], p['bev_y']] for p in trajectory])
        
        # Use only the last window_size points
        if len(pts) > self.window_size:
            pts_win = pts[-self.window_size:]
        else:
            pts_win = pts
            
        if len(pts_win) < 15: # Minimum for Savitzky-Golay
            return {}
            
        smoothed = smooth_trajectory(pts_win)
        
        # 2. Compute Velocity and Derivatives
        dt = 1.0 / self.fps
        dx = np.diff(smoothed[:, 0])
        dy = np.diff(smoothed[:, 1])
        vel = np.sqrt(dx**2 + dy**2) / dt
        accel = np.diff(vel) / dt
        jerk = np.diff(accel) / dt
        
        # 3. Compute Orientation (Heading)
        heading = np.arctan2(dy, dx)
        heading_diff = np.diff(heading)
        # Normalize diff to [-pi, pi]
        heading_diff = (heading_diff + np.pi) % (2 * np.pi) - np.pi
        
        features = {}
        
        # --- FEATURE 1: SDLP (Standard Deviation of Lateral Position) ---
        if len(smoothed) > 10:
            vec_long = smoothed[-1] - smoothed[0]
            if np.linalg.norm(vec_long) > 1e-3:
                vec_lat = np.array([-vec_long[1], vec_long[0]])
                vec_lat = vec_lat / np.linalg.norm(vec_lat)
                # Project all points onto lateral vector
                lat_positions = np.dot(smoothed - smoothed[0], vec_lat)
                features['sdlp'] = float(np.std(lat_positions))
                
                # --- FEATURE 2: Lateral Band Energy (High-freq drifting) ---
                if len(lat_positions) >= 30:
                    y_fft = fft(lat_positions - np.mean(lat_positions))
                    energy = np.abs(y_fft)**2
                    # Energy in top 40% of frequencies
                    cutoff = int(len(energy) * 0.6)
                    high_freq_energy = np.sum(energy[cutoff:])
                    total_energy = np.sum(energy) + 1e-6
                    features['lateral_band_energy'] = float(high_freq_energy / total_energy)
                else:
                    features['lateral_band_energy'] = 0.0

        # --- FEATURE 3: Steering Entropy ---
        if len(heading_diff) > 10:
            hist, _ = np.histogram(heading_diff, bins=10, density=True)
            hist = hist[hist > 0]
            entropy = -np.sum(hist * np.log(hist + 1e-9))
            features['steering_entropy'] = float(entropy)
        else:
            features['steering_entropy'] = 0.0
            
        # --- FEATURE 4: Speed CV (Coefficient of Variation) ---
        if len(vel) > 10:
            avg_v = np.mean(vel)
            if avg_v > 0.1:
                features['speed_cv'] = float(np.std(vel) / avg_v)
            else:
                features['speed_cv'] = 0.0
        else:
            features['speed_cv'] = 0.0
                
        # --- FEATURE 5: Jerk RMS ---
        if len(jerk) > 5:
            features['jerk_rms'] = float(np.sqrt(np.mean(jerk**2)))
        else:
            features['jerk_rms'] = 0.0
            
        return features
