import cv2
import base64
import numpy as np
from . import overlay_api as ov

# Normalized coordinates for the 4 markers (top-left, top-right, bottom-right, bottom-left)
# Using a margin so they aren't completely cut off by the edge of the iPad screen.
MARGIN = 0.05
SIZE = 0.20 # 20% of the shortest screen dimension (so it's a perfect square)

# Since we will use 'size' instead of w/h, the aspect ratio is perfectly 1:1 on the iPad.
# We also want the right and bottom markers to align correctly.
# If size=0.15 is relative to the minimum dimension (usually height on landscape),
# then on the X axis, 0.15 * H is smaller than 0.15 * W. 
# We'll just define the coordinates, but keep in mind (1.0 - MARGIN) will be the anchor.

def generate_and_display_markers():
    """Generates 4 ArUco markers and pushes them to the overlay engine."""
    dict_aruco = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    
    # We will use explicit normalized anchors, and let the iPad renderer draw them.
    # To keep the homography mapping extremely accurate, we need to know the EXACT normalized 
    # corners of these markers on the iPad screen.
    # If the iPad draws them at (x, y) with width=S, height=S (in pixels), we don't know the exact 
    # normalized (0-1) coordinates of the bottom-right corner of the marker unless we know the iPad's aspect ratio.
    # Therefore, we MUST pass `w` and `h` in normalized 0-1 coordinates, even if it looks slightly stretched on the iPad.
    # ArUco detection handles affine/perspective distortion perfectly fine!
    
    MARKER_POSITIONS = {
        0: (MARGIN, MARGIN),               
        1: (1.0 - MARGIN - SIZE, MARGIN),  
        2: (1.0 - MARGIN - SIZE, 1.0 - MARGIN - SIZE), 
        3: (MARGIN, 1.0 - MARGIN - SIZE)   
    }
    
    for marker_id, (norm_x, norm_y) in MARKER_POSITIONS.items():
        # Generate 200x200 pixel marker
        marker_img = cv2.aruco.generateImageMarker(dict_aruco, marker_id, 200)
        
        # Add a white border so it's easily detectable even on dark backgrounds
        marker_img = cv2.copyMakeBorder(marker_img, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
        
        # Encode to Base64
        _, buf = cv2.imencode('.jpg', marker_img)
        b64 = base64.b64encode(buf).decode('ascii')
        src = f"data:image/jpeg;base64,{b64}"
        
        # Push to overlay
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
        
        # The 4 corners of the marker in normalized space (TL, TR, BR, BL)
        corners[marker_id] = np.array([
            [nx, ny],                   # Top-Left
            [nx + SIZE, ny],            # Top-Right
            [nx + SIZE, ny + SIZE],     # Bottom-Right
            [nx, ny + SIZE]             # Bottom-Left
        ], dtype=np.float32)
    return corners

def hide_calibration_markers(keep_anchor=True):
    """Hides markers 1, 2, and 3 after calibration so they don't clutter the iPad screen."""
    for marker_id in [1, 2, 3]:
        ov.remove(f"aruco_{marker_id}")
    if not keep_anchor:
        ov.remove("aruco_0")
