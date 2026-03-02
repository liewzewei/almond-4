import cv2
import logging
from typing import Tuple, Any, Optional

class VideoProcessor:
    def __init__(self, video_path: str, target_size=(1280, 720), crop_top_ratio=0.3):
        self.video_path = video_path
        self.target_size = target_size
        self.crop_top_ratio = crop_top_ratio
        
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
            
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        if self.fps <= 0:
            self.fps = 25.0 # Fallback
            logging.warning("FPS could not be determined from video. defaulting to 25.0")
        
        self.crop_y0 = int(self.height * self.crop_top_ratio)
        self.cropped_height = self.height - self.crop_y0
        
        # Scale factors to map processed coords back to original if needed
        self.scale_x = self.target_size[0] / self.width
        self.scale_y = self.target_size[1] / self.cropped_height
        
        logging.info(f"Video initialized: {self.width}x{self.height} @ {self.fps} FPS")

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, None
            
        # Crop bottom 70% (top 30% removed)
        cropped = frame[self.crop_y0:, :, :]
        
        # Resize to target
        resized = cv2.resize(cropped, self.target_size, interpolation=cv2.INTER_LINEAR)
        
        return frame, resized

    def release(self):
        self.cap.release()
