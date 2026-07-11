import cv2
import numpy as np
import os

CHECKERBOARD = (8, 5)
SQUARE_SIZE = 3.0 # cm

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE

objpoints = []
imgpoints_left = []
imgpoints_right = []

valid_pairs = 0
img_size = None

import glob
import re

image_files = glob.glob("calib/t_*.jpg")
indices = [int(re.search(r't_(\d+)', f).group(1)) for f in image_files]

for i in indices:
    img_l_path = f"calib/t_{i}.jpg"
    img_r_path = f"calib/s_{i}.jpg"
    
    if not os.path.exists(img_l_path) or not os.path.exists(img_r_path):
        continue

    img_l = cv2.imread(img_l_path)
    img_r = cv2.imread(img_r_path)
    
    if img_l is None or img_r is None:
        continue
        
    gray_l = cv2.cvtColor(img_l, cv2.COLOR_BGR2GRAY)
    gray_r = cv2.cvtColor(img_r, cv2.COLOR_BGR2GRAY)
    
    if img_size is None:
        img_size = gray_l.shape[::-1]

    ret_l, corners_l = cv2.findChessboardCorners(gray_l, CHECKERBOARD, None)
    ret_r, corners_r = cv2.findChessboardCorners(gray_r, CHECKERBOARD, None)

    if ret_l and ret_r:
        objpoints.append(objp)
        corners2_l = cv2.cornerSubPix(gray_l, corners_l, (11, 11), (-1, -1), criteria)
        imgpoints_left.append(corners2_l)
        corners2_r = cv2.cornerSubPix(gray_r, corners_r, (11, 11), (-1, -1), criteria)
        imgpoints_right.append(corners2_r)
        valid_pairs += 1

print(f"Found {valid_pairs} valid image pairs with checkerboard fully visible out of 64.")

if valid_pairs < 5:
    print("Not enough valid pairs to calibrate. Check if the checkerboard is fully visible or if the grid dimensions are exactly 8x5 inner corners.")
    exit(1)

print("Calibrating left camera...")
ret_l, mtx_l, dist_l, rvecs_l, tvecs_l = cv2.calibrateCamera(objpoints, imgpoints_left, img_size, None, None)
print("Calibrating right camera...")
ret_r, mtx_r, dist_r, rvecs_r, tvecs_r = cv2.calibrateCamera(objpoints, imgpoints_right, img_size, None, None)

print("Performing stereo calibration...")
flags = cv2.CALIB_FIX_INTRINSIC
ret_stereo, mtx_l, dist_l, mtx_r, dist_r, R, T, E, F = cv2.stereoCalibrate(
    objpoints, imgpoints_left, imgpoints_right,
    mtx_l, dist_l, mtx_r, dist_r,
    img_size, criteria=criteria, flags=flags)

print("Stereo reprojection error:", ret_stereo)

R1, R2, P1, P2, Q, roi_left, roi_right = cv2.stereoRectify(
    mtx_l, dist_l, mtx_r, dist_r, img_size, R, T, flags=cv2.CALIB_ZERO_DISPARITY, alpha=-1)

np.savez("stereo.npz", P0=P1, P1=P2, R=R, T=T, mtx0=mtx_l, dist0=dist_l, mtx1=mtx_r, dist1=dist_r)
print("Saved stereo.npz successfully! Ready for 3D tracking.")
