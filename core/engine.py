import logging
from typing import List, Dict, Any

from .perception.homography import HomographyEstimator
from .perception.bev_transform import BEVTransformer
from .motion.trajectory_manager import TrajectoryManager
from .motion.features import FeatureEngine
from .statistics.robust_baseline import OnlineRobustBaseline
from .statistics.probability import RiskProbabilityConverter
from .statistics.risk_fusion import RiskFusionEngine

class RiskEngine:
    """
    Main orchestrator for the research-grade vehicle risk detection pipeline.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fps = config.get('fps', 30.0)
        
        # Modules
        self.homography_estimator = HomographyEstimator(config.get('homography_recompute_sec', 10))
        self.bev_transformer = BEVTransformer()
        self.trajectory_manager = TrajectoryManager(max_points=int(self.fps * 5)) # 5s history
        self.feature_engine = FeatureEngine(fps=self.fps, window_sec=3.0)
        self.baseline = OnlineRobustBaseline(min_samples=config.get('min_samples', 30))
        self.prob_converter = RiskProbabilityConverter()
        self.risk_fusion = RiskFusionEngine(
            weights=config.get('weights'), 
            alpha=config.get('fusion_alpha', 0.4),
            alert_threshold=config.get('alert_risk_threshold', 0.85)
        )
        
        # Latest results state
        self.latest_risks: Dict[int, float] = {}
        self.latest_features: Dict[int, Dict[str, float]] = {}
        self.latest_probs: Dict[int, Dict[str, float]] = {}
        
    def update_alert_threshold(self, new_threshold: float):
        """Allows dynamic updates from UI or external components."""
        self.risk_fusion.alert_threshold = new_threshold
        
    def process_frame(self, frame, tracks: List[dict], frame_idx: int, timestamp: float) -> List[dict]:
        """
        Processes a single frame:
        1. Update Homography
        2. BEV Transformation & Trajectory Update
        3. Feature Extraction
        4. Probability Mapping
        5. Risk Fusion
        6. Baseline Adaptation
        """
        # 1. Homography update (periodic internals)
        h_matrix = self.homography_estimator.update(frame, timestamp)
        
        # 2. Update Trajectories in BEV space
        active_ids = self.trajectory_manager.update(
            tracks, frame_idx, timestamp, 
            bev_transformer=self.bev_transformer, 
            h_matrix=h_matrix
        )
        
        results = []
        for track in tracks:
            tid = track['track_id']
            trajectory = self.trajectory_manager.get_trajectory(tid)
            
            # 3. Feature Computation
            features = self.feature_engine.compute_features(trajectory)
            if not features:
                continue
            
            # 4. Probability Computation (requires baseline)
            # Use cached medians/sigmas from baseline
            medians = self.baseline.medians
            sigmas = self.baseline.sigmas
            
            probs = self.prob_converter.compute_probabilities(features, medians, sigmas)
            
            # 5. Risk Fusion
            risk_score = self.risk_fusion.fuse(tid, probs, self.fps)
            is_alert = self.risk_fusion.check_alert(tid, risk_score, self.fps)
            
            # 6. Baseline Adaptation (Phase 9: Protect baseline from outliers)
            self.baseline.update(features, risk_score)
            
            # Collect results
            self.latest_risks[tid] = risk_score
            self.latest_features[tid] = features
            self.latest_probs[tid] = probs
            
            results.append({
                "track_id": tid,
                "risk_score": risk_score,
                "is_alert": is_alert,
                "features": features,
                "probabilities": probs,
                "bbox": track["bbox"]
            })
            
        # Cleanup history for lost tracks
        self.risk_fusion.cleanup(active_ids)
        
        return results
