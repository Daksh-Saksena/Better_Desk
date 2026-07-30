import cv2
import base64
import numpy as np
from . import overlay_api as ov
MARGIN = 0.05
SIZE = 0.20
def generate_and_display_markers():
    """Generates 4 ArUco markers and pushes them to the overlay engine."""
    dict_aruco = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    MARKER_POSITIONS = {
        0: (MARGIN, MARGIN),               
        1: (1.0 - MARGIN - SIZE, MARGIN),  
        2: (1.0 - MARGIN - SIZE, 1.0 - MARGIN - SIZE), 
        3: (MARGIN, 1.0 - MARGIN - SIZE)   
    }
    for marker_id, (norm_x, norm_y) in MARKER_POSITIONS.items():
        marker_img = cv2.aruco.generateImageMarker(dict_aruco, marker_id, 200)
        marker_img = cv2.copyMakeBorder(marker_img, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
        _, buf = cv2.imencode('.jpg', marker_img)
        b64 = base64.b64encode(buf).decode('ascii')
        src = f"data:image/jpeg;base64,{b64}"
        ov.draw_image(
            x=norm_x, 
            y=norm_y, 
            w=SIZE, 
            h=SIZE, 
            src=src, 
            id_=f"aruco_{marker_id}", 
            layer=0
        )
def get_marker_normalized_corners():
    """
    Returns the exact normalized (0.0 to 1.0) coordinates of the 4 corners of each marker 
    on the iPad screen, assuming they were drawn with w=SIZE and h=SIZE.
    This is used by detector.py as the destination points (dst_pts) for Homography.
    Returns: Dict[marker_id, np.ndarray(4, 2)]
    """
    corners = {}
    for marker_id in [0, 1, 2, 3]:
        nx = MARGIN if marker_id in [0, 3] else (1.0 - MARGIN - SIZE)
        ny = MARGIN if marker_id in [0, 1] else (1.0 - MARGIN - SIZE)
        corners[marker_id] = np.array([
            [nx, ny],
            [nx + SIZE, ny],
            [nx + SIZE, ny + SIZE],
            [nx, ny + SIZE]
        ], dtype=np.float32)
    return corners
def hide_calibration_markers(keep_anchor=True):
    """Hides markers 1, 2, and 3 after calibration so they don't clutter the iPad screen."""
    for marker_id in [1, 2, 3]:
        ov.remove(f"aruco_{marker_id}")
    if not keep_anchor:
        ov.remove("aruco_0")
