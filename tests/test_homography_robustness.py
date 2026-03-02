import cv2
import numpy as np
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.perception.homography import HomographyEstimator

def create_synthetic_highway(w=1280, h=720):
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    # Background (dark gray road)
    cv2.rectangle(frame, (0, 0), (w, h), (40, 40, 40), -1)
    
    # Left lane line (white, converging)
    # Start at bottom left, go towards VP (middle-top)
    # (200, 719) to (500, 288)
    cv2.line(frame, (200, h-1), (500, int(h*0.4)), (255, 255, 255), 10)
    
    # Right lane line (white, converging)
    # Start at bottom right, go towards VP (middle-top)
    # (1080, 719) to (780, 288)
    cv2.line(frame, (1080, h-1), (780, int(h*0.4)), (255, 255, 255), 10)
    
    # Add some "noise" above horizon
    cv2.rectangle(frame, (0, 0), (w, int(h*0.4)), (150, 100, 50), -1) # Sky/Landscape
    
    return frame

def test_robustness():
    logging.basicConfig(level=logging.INFO)
    print("Testing Homography Robustness...")
    
    config = {
        'homography_recompute_sec': 0, # Force update
        'hough_threshold': 30,
        'hough_min_line_len': 40,
        'hough_max_line_gap': 50,
        'roi_top_perc': 0.4
    }
    
    estimator = HomographyEstimator(config)
    frame = create_synthetic_highway()
    
    # First update
    matrix = estimator.update(frame, 1.0)
    
    if matrix is not None:
        print("Success: Homography matrix generated!")
        print(f"Confidence score: {estimator.confidence_score}")
        
        # Verify matrix is not just identity (though it shouldn't be anyway)
        if np.allclose(matrix, np.eye(3)):
            print("Failure: Matrix is identity")
            sys.exit(1)
        else:
            print("Matrix seems valid.")
    else:
        print("Failure: Homography matrix is None")
        # Save frame to debug if it fails
        cv2.imwrite("failed_test_frame.png", frame)
        print("Saved failed_test_frame.png for debugging.")
        sys.exit(1)

if __name__ == "__main__":
    test_robustness()
