import yaml
import os

class Config:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r') as f:
            self.raw_config = yaml.safe_load(f)
            
        # UI/Server Config
        self.HOST = "0.0.0.0"
        self.PORT = 5000
        self.DEBUG = False
        
        # Paths
        self.UPLOADS_DIR = "uploads"
        self.SNAPSHOTS_DIR = "snapshots"
        
        # Ensure dirs exist
        os.makedirs(self.UPLOADS_DIR, exist_ok=True)
        os.makedirs(self.SNAPSHOTS_DIR, exist_ok=True)
        
        # AI Config
        self.YOLO_MODEL = self.raw_config.get('yolo_model', 'yolov8n.pt')
        self.TRACKER_TYPE = self.raw_config.get('tracker_type', 'bytetrack.yaml')
        self.CONF_THRESHOLD = self.raw_config.get('yolo_conf_threshold', 0.25)
        self.ALERT_THRESHOLD = self.raw_config.get('alert_risk_threshold', 0.85)
        self.HOMOGRAPHY_SEC = self.raw_config.get('homography_recompute_sec', 15)
        
    def get(self, key, default=None):
        return self.raw_config.get(key, default)

config = Config()
