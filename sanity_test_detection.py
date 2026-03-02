import cv2
import torch
from core.detector import Detector

def test_detection():
    print("Testing Detection...")
    detector = Detector()
    # Create a dummy frame
    frame = (torch.rand((720, 1280, 3)) * 255).numpy().astype('uint8')
    detections = detector.detect(frame)
    print(f"Inference successful. Detections count: {len(detections)}")
    print("Success!")

if __name__ == "__main__":
    test_detection()
