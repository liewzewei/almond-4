import cv2
import numpy as np

class BEVTransformer:
    """
    Handles transformation of image pixel coordinates to BEV coordinates.
    """
    def __init__(self):
        pass
        
    def transform_point(self, point_pixel, homography_matrix):
        """
        Transforms a single [x, y] point to BEV coordinates.
        """
        if homography_matrix is None:
            return point_pixel
            
        pts = np.float32([point_pixel]).reshape(-1, 1, 2)
        transformed = cv2.perspectiveTransform(pts, homography_matrix)
        return transformed[0][0]
        
    def transform_points(self, points_pixel, homography_matrix):
        """
        Transforms a list of [x, y] points to BEV coordinates.
        """
        if homography_matrix is None:
            return points_pixel
            
        pts = np.float32(points_pixel).reshape(-1, 1, 2)
        transformed = cv2.perspectiveTransform(pts, homography_matrix)
        return transformed.reshape(-1, 2)
