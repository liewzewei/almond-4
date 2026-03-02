import numpy as np
from scipy.signal import savgol_filter

def smooth_trajectory(points, window_length=15, polyorder=3):
    """
    Applies Savitzky-Golay filtering to a set of points [[x,y], [x,y], ...].
    """
    if len(points) < window_length:
        return np.array(points)
        
    pts = np.array(points)
    x = pts[:, 0]
    y = pts[:, 1]
    
    # window_length must be odd
    if window_length % 2 == 0:
        window_length += 1
        
    smooth_x = savgol_filter(x, window_length, polyorder)
    smooth_y = savgol_filter(y, window_length, polyorder)
    
    return np.stack([smooth_x, smooth_y], axis=1)
