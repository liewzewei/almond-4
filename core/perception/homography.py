import cv2
import numpy as np
import time
import logging

class HomographyEstimator:
    def __init__(self, recompute_interval_sec=10):
        self.recompute_interval_sec = recompute_interval_sec
        self.last_update_time = 0
        self.homography_matrix = None
        self.confidence_score = 0.0
        
        # Target BEV dimensions
        self.bev_width = 1000
        self.bev_height = 1500
        
    def update(self, frame, timestamp):
        """
        Periodically updates the homography matrix using lane detection.
        """
        if self.homography_matrix is not None and (timestamp - self.last_update_time) < self.recompute_interval_sec:
            return self.homography_matrix
            
        logging.info(f"Attempting homography update at {timestamp:.2f}s")
        
        # 1. Preprocess
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 2. Edge Detection
        edges = cv2.Canny(blur, 50, 150)
        
        # 3. Hough Line Transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=100, maxLineGap=20)
        
        if lines is None or len(lines) < 2:
            logging.warning("Insufficient lines for homography estimation")
            return self.homography_matrix
            
        # 4. Filter and Cluster Lines
        left_lines = []
        right_lines = []
        h, w = frame.shape[:2]
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 == x1: continue
            slope = (y2 - y1) / (x2 - x1)
            
            # Filter by slope (standard for high-angle highway)
            if 0.3 < abs(slope) < 2.0:
                if slope < 0:
                    left_lines.append(line[0])
                else:
                    right_lines.append(line[0])
                    
        if len(left_lines) < 1 or len(right_lines) < 1:
            logging.warning("Could not find both left and right lane clusters")
            return self.homography_matrix
            
        # 5. Average Clusters & Vanishing Point
        def get_avg_line(cluster_lines):
            avg = np.mean(cluster_lines, axis=0)
            return avg.astype(int)
            
        l_avg = get_avg_line(left_lines)
        r_avg = get_avg_line(right_lines)
        
        def line_intersection(line1, line2):
            x1, y1, x2, y2 = line1
            x3, y3, x4, y4 = line2
            denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
            if denom == 0: return None
            ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
            return int(x1 + ua * (x2 - x1)), int(y1 + ua * (y2 - y1))
            
        vp = line_intersection(l_avg, r_avg)
        
        # 6. Validation
        if vp is None or not (0 <= vp[0] <= w and 0 <= vp[1] <= h * 0.5):
            logging.warning(f"Invalid vanishing point: {vp}")
            return self.homography_matrix
            
        # 7. Define Road Trapezoid to Rectangle Mapping
        # Use simple fixed trapezoid relative to vanishing point for MVP
        src_pts = np.float32([
            [l_avg[0], l_avg[1]], # Top Left
            [r_avg[0], r_avg[1]], # Top Right
            [l_avg[2], l_avg[3]], # Bottom Left
            [r_avg[2], r_avg[3]]  # Bottom Right
        ])
        
        dst_pts = np.float32([
            [0, 0],
            [self.bev_width, 0],
            [0, self.bev_height],
            [self.bev_width, self.bev_height]
        ])
        
        new_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        
        # Update state
        self.homography_matrix = new_matrix
        self.last_update_time = timestamp
        self.confidence_score = 0.8 # Basic fixed confidence for MVP
        logging.info("Homography updated successfully")
        
        return self.homography_matrix
