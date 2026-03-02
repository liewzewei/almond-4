import cv2
import logging
from typing import Tuple, Any, Optional

class VideoProcessor:
    def __init__(self, video_path: str):
        self.video_path = video_path
        
        # Determine if source is live camera (int) or file (str)
        try:
            source = int(video_path)
            logging.info(f"Using live camera index: {source}")
        except ValueError:
            source = video_path
            logging.info(f"Using video file: {source}")
            
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video source: {video_path}")
            
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        if self.fps <= 0:
            self.fps = 25.0 # Fallback
            logging.warning("FPS could not be determined from source. defaulting to 25.0")
        
        # Scale factors are 1.0 because we work on raw pixels
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        logging.info(f"Video Source initialized: {self.width}x{self.height} @ {self.fps} FPS")

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
            
        return frame

    def release(self):
        self.cap.release()
