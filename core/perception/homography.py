import cv2
import numpy as np
import time
import logging

class HomographyEstimator:
    def __init__(self, config=None):
        if config is None:
            config = {}
        # Support both old (int) and new (dict) init for safety
        if isinstance(config, (int, float)):
            self.recompute_interval_sec = config
            self.hough_threshold = 50
            self.hough_min_line_len = 100
            self.hough_max_line_gap = 20
            self.roi_top_perc = 0.4
        else:
            self.recompute_interval_sec = config.get('homography_recompute_sec', 15)
            self.hough_threshold = config.get('hough_threshold', 40)
            self.hough_min_line_len = config.get('hough_min_line_len', 60)
            self.hough_max_line_gap = config.get('hough_max_line_gap', 40)
            self.roi_top_perc = config.get('roi_top_perc', 0.4)
            
        self.last_update_time = 0
        self.homography_matrix = None
        self.confidence_score = 0.0
        
        # Target BEV dimensions
        self.bev_width = 1000
        self.bev_height = 1500
        
    def _detect_lines(self, edges):
        # Try multiple parameter sets if needed
        params = [
            # Standard (User provided)
            (self.hough_threshold, self.hough_min_line_len, self.hough_max_line_gap),
            # More relaxed
            (int(self.hough_threshold * 0.7), int(self.hough_min_line_len * 0.7), int(self.hough_max_line_gap * 1.5)),
            # Very aggressive
            (20, 30, 60)
        ]
        
        for thresh, minlen, maxgap in params:
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=thresh, minLineLength=minlen, maxLineGap=maxgap)
            if lines is not None and len(lines) >= 2:
                logging.debug(f"Detected {len(lines)} lines with params: {thresh}/{minlen}/{maxgap}")
                return lines
        return None

    def update(self, frame, timestamp):
        """
        Periodically updates the homography matrix using lane detection.
        """
        if self.homography_matrix is not None and (timestamp - self.last_update_time) < self.recompute_interval_sec:
            return self.homography_matrix
            
        logging.info(f"Attempting homography update at {timestamp:.2f}s")
        h, w = frame.shape[:2]
        
        # 1. Preprocess
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply ROI Mask (ignore top part of the image)
        mask = np.zeros_like(gray)
        roi_y = int(h * self.roi_top_perc)
        mask[roi_y:, :] = 255
        
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 2. Edge Detection - Try multiple Canny thresholds
        canny_params = [(50, 150), (30, 100), (20, 60)]
        lines = None
        
        for low, high in canny_params:
            edges = cv2.Canny(blur, low, high)
            edges = cv2.bitwise_and(edges, mask)
            lines = self._detect_lines(edges)
            if lines is not None:
                logging.debug(f"Success with Canny thresholds: {low}/{high}")
                break
        
        if lines is None:
            logging.warning("No lines detected even with fallback parameters")
            return self.homography_matrix
            
        logging.info(f"Detected {len(lines)} raw lines in ROI")
            
        # 4. Filter and Cluster Lines
        h, w = frame.shape[:2]
        left_lines = []
        right_lines = []
        
        for i, line in enumerate(lines):
            x1, y1, x2, y2 = line[0]
            
            # Calculate slope with vertical handling
            if x2 == x1:
                slope = 999.0 if (y2 > y1) else -999.0 # Pointing down (+) or up (-)
            else:
                slope = (y2 - y1) / (x2 - x1)
            
            # Extremely relaxed slope range: 0.01 to 1000.0
            if 0.01 < abs(slope) < 1000.0:
                if slope < 0:
                    left_lines.append(line[0])
                else:
                    right_lines.append(line[0])
            else:
                logging.info(f"Line {i}: slope {slope:.2f} rejected (range 0.01-1000.0)")
        
        logging.info(f"Slope-based clusters: left={len(left_lines)}, right={len(right_lines)}")
                    
        # Fallback: if slope-based clustering fails but we have lines, use image position
        if (len(left_lines) < 1 or len(right_lines) < 1) and len(lines) >= 2:
            logging.info("Slope clustering failed, falling back to position-based clustering")
            left_lines = []
            right_lines = []
            # Sort lines by their average X position
            sorted_lines = sorted(lines, key=lambda l: (l[0][0] + l[0][2]) / 2)
            mid = len(sorted_lines) // 2
            for i, line in enumerate(sorted_lines):
                if i < mid:
                    left_lines.append(line[0])
                else:
                    right_lines.append(line[0])
            logging.info(f"Position-based clusters: left={len(left_lines)}, right={len(right_lines)}")

        if len(left_lines) < 1 or len(right_lines) < 1:
            logging.warning("Insufficient lane clusters for homography estimation")
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
        if vp is None or not (-w * 0.5 <= vp[0] <= w * 1.5 and 0 <= vp[1] <= h * 0.8):
            logging.warning(f"Invalid vanishing point: {vp}")
            return self.homography_matrix
            
        # 7. Define Road Trapezoid dynamically
        def get_points_on_line(line, y_top, y_bottom):
            x1, y1, x2, y2 = line
            if y2 == y1: return (x1, y_top), (x1, y_bottom) # Vertical
            slope_inv = (x2 - x1) / (y2 - y1)
            x_top = x1 + (y_top - y1) * slope_inv
            x_bottom = x1 + (y_bottom - y1) * slope_inv
            return (int(x_top), int(y_top)), (int(x_bottom), int(y_bottom))

        # Use 10% below vanishing point and bottom of frame
        y_top = vp[1] + int(h * 0.1)
        y_bottom = h - 1
        
        l_top, l_bot = get_points_on_line(l_avg, y_top, y_bottom)
        r_top, r_bot = get_points_on_line(r_avg, y_top, y_bottom)
        
        src_pts = np.float32([
            l_top, # Top Left
            r_top, # Top Right
            l_bot, # Bottom Left
            r_bot  # Bottom Right
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
        self.confidence_score = 0.8
        logging.info(f"Homography updated dynamically. VP: {vp}")
        
        return self.homography_matrix
