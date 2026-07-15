import cv2 as c
import numpy as n
from mediapipe.tasks import python as p
from mediapipe.tasks.python import vision as v
import mediapipe as m
import sys as y
import threading as t
import base64 as b
import requests as r
import math

try:
    st = n.load("stereo.npz")
    p0 = st["P0"]
    p1 = st["P1"]
except:
    y.exit()

idx0 = 0
idx1 = 2
c0 = c.VideoCapture(idx0)
c1 = c.VideoCapture(idx1)

o = v.HandLandmarkerOptions(
    base_options=p.BaseOptions(model_asset_path='hand_landmarker.task'),
    running_mode=v.RunningMode.IMAGE,
    num_hands=2
)
d = v.HandLandmarker.create_from_options(o)
cn = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(17,18),(18,19),(19,20),(0,17)]

bd0 = []
bd1 = []
cf0 = None
cf1 = None
a = True

def wk(cam_id):
    global bd0, bd1
    s = r.Session()
    u = 'https://detect.roboflow.com/find-battery-current-vzeoc/2'
    q = {'api_key': '84aau744LSxt5mDCmfY4'}
    while a:
        cf = cf0 if cam_id == 0 else cf1
        if cf is not None:
            try:
                cs = cf.copy()
                h, w = cs.shape[:2]
                sm = c.resize(cs, (320, 240))
                _, bf = c.imencode('.jpg', sm)
                b6 = b.b64encode(bf).decode('ascii')
                rs = s.post(u, params=q, data=b6, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=5).json()
                ps = rs.get('predictions', [])
                nb = []
                for pr in ps:
                    if pr['confidence'] > 0.5:
                        x, y, w_, h_ = pr['x'], pr['y'], pr['width'], pr['height']
                        x1 = int((x - w_ / 2) * w / 320.0)
                        y1 = int((y - h_ / 2) * h / 240.0)
                        x2 = int((x + w_ / 2) * w / 320.0)
                        y2 = int((y + h_ / 2) * h / 240.0)
                        nb.append((x1, y1, x2, y2, pr['class'], pr['confidence']))
                if cam_id == 0: bd0 = nb
                else: bd1 = nb
            except Exception as e:
                print(f"API Error (Cam {cam_id}):", e)
        import time
        time.sleep(0.2)

t.Thread(target=wk, args=(0,), daemon=True).start()
t.Thread(target=wk, args=(1,), daemon=True).start()

import os, json
rot_file = 'rot_config.json'
if os.path.exists(rot_file):
    with open(rot_file, 'r') as f:
        cfg = json.load(f)
        rot0 = cfg.get('rot0', 0)
        rot1 = cfg.get('rot1', 0)
else:
    rot0 = 0
    rot1 = 0

def save_rot():
    with open(rot_file, 'w') as f: json.dump({'rot0': rot0, 'rot1': rot1}, f)

img_c = 0
btn_cl = False
cam_mode = 0
def m_cb(e, x, y, f, p):
    global btn_cl
    if e == c.EVENT_LBUTTONDOWN and 10 <= x <= 160 and 10 <= y <= 60: btn_cl = True
c.namedWindow("Duo")
c.setMouseCallback("Duo", m_cb)

while True:
    ok0, r0 = c0.read()
    ok1, r1 = c1.read()
    
    if not ok0 or r0 is None:
        r0 = n.zeros((480, 640, 3), dtype=n.uint8)
        c.putText(r0, "NO CAM %d" % idx0, (50, 240), c.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
    if not ok1 or r1 is None:
        r1 = n.zeros((480, 640, 3), dtype=n.uint8)
        c.putText(r1, "NO CAM %d" % idx1, (50, 240), c.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
    
    if rot0 == 1: r0 = c.rotate(r0, c.ROTATE_90_CLOCKWISE)
    elif rot0 == 2: r0 = c.rotate(r0, c.ROTATE_180)
    elif rot0 == 3: r0 = c.rotate(r0, c.ROTATE_90_COUNTERCLOCKWISE)
    
    if rot1 == 1: r1 = c.rotate(r1, c.ROTATE_90_CLOCKWISE)
    elif rot1 == 2: r1 = c.rotate(r1, c.ROTATE_180)
    elif rot1 == 3: r1 = c.rotate(r1, c.ROTATE_90_COUNTERCLOCKWISE)
    
    o0 = r0.copy()
    o1 = r1.copy()
    
    f0 = c.resize(r0, (int(480 * r0.shape[1] / r0.shape[0]), 480))
    f1 = c.resize(r1, (int(480 * r1.shape[1] / r1.shape[0]), 480))
    cf0 = f0.copy()
    cf1 = f1.copy()
    f0_h, f0_w = f0.shape[:2]
    f1_h, f1_w = f1.shape[:2]
    
    for x1, y1, x2, y2, lb, co in bd0:
        c.rectangle(f0, (x1, y1), (x2, y2), (0, 255, 0), 2)
        c.putText(f0, "%s %.2f" % (lb, co), (x1, y1 - 10), c.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
    for x1, y1, x2, y2, lb, co in bd1:
        c.rectangle(f1, (x1, y1), (x2, y2), (0, 255, 0), 2)
        c.putText(f1, "%s %.2f" % (lb, co), (x1, y1 - 10), c.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
    r0 = c.cvtColor(f0, c.COLOR_BGR2RGB)
    r1 = c.cvtColor(f1, c.COLOR_BGR2RGB)
    
    pt0 = None
    pt1 = None
    
    if cam_mode in [0, 1]:
        hr0 = d.detect(m.Image(image_format=m.ImageFormat.SRGB, data=r0))
        if hr0.hand_landmarks:
            h0 = hr0.hand_landmarks[0]
            for p1_, p2_ in cn:
                c.line(f0, (int(h0[p1_].x * f0_w), int(h0[p1_].y * f0_h)), (int(h0[p2_].x * f0_w), int(h0[p2_].y * f0_h)), (0, 255, 0), 2)
            for i in [4, 8, 12, 16, 20]:
                cx, cy = int(h0[i].x * f0_w), int(h0[i].y * f0_h)
                c.circle(f0, (cx, cy), 8, (0, 0, 255), -1)
            pt0 = (int(h0[8].x * f0_w), int(h0[8].y * f0_h))
            
            p_obj = 'None'
            for bx1, by1, bx2, by2, lb, co in bd0:
                if bx1 <= pt0[0] <= bx2 and by1 <= pt0[1] <= by2:
                    p_obj = lb
                    break
            c.putText(f0, "Pointing at: %s" % p_obj, (10, f0_h - 10), c.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    if cam_mode in [0, 2]:
        hr1 = d.detect(m.Image(image_format=m.ImageFormat.SRGB, data=r1))
        if hr1.hand_landmarks:
            h1 = hr1.hand_landmarks[0]
            for p1_, p2_ in cn:
                c.line(f1, (int(h1[p1_].x * f1_w), int(h1[p1_].y * f1_h)), (int(h1[p2_].x * f1_w), int(h1[p2_].y * f1_h)), (0, 255, 0), 2)
            for i in [4, 8, 12, 16, 20]:
                cx, cy = int(h1[i].x * f1_w), int(h1[i].y * f1_h)
                c.circle(f1, (cx, cy), 8, (0, 0, 255), -1)
            pt1 = (int(h1[8].x * f1_w), int(h1[8].y * f1_h))
            
            p_obj1 = 'None'
            for bx1, by1, bx2, by2, lb, co in bd1:
                if bx1 <= pt1[0] <= bx2 and by1 <= pt1[1] <= by2:
                    p_obj1 = lb
                    break
            c.putText(f1, "Pointing at: %s" % p_obj1, (10, f1_h - 10), c.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    lx, ly, lz = None, None, None
    if cam_mode == 0 and pt0 and pt1:
        pts = c.triangulatePoints(p0, p1, n.array([[pt0[0]], [pt0[1]]], dtype=n.float32), n.array([[pt1[0]], [pt1[1]]], dtype=n.float32))
        pts /= pts[3]
        lx, ly, lz = pts[0, 0], pts[1, 0], pts[2, 0]
        c.putText(f0, "3D: X=%.1f Y=%.1f Z=%.1f" % (lx, ly, lz), (20, 80), c.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    if cam_mode == 0:
        cm = c.hconcat([f0, f1])
        c.rectangle(cm, (10, 10), (160, 60), (0, 0, 255), -1)
        c.putText(cm, "CAPTURE", (25, 45), c.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        c.putText(cm, "Captured: %d" % img_c, (10, 90), c.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    elif cam_mode == 1:
        cm = f0
    elif cam_mode == 2:
        cm = f1

    if btn_cl:
        import os
        if not os.path.exists('calib'): os.makedirs('calib')
        c.imwrite('calib/t_%d.jpg' % img_c, o0)
        c.imwrite('calib/s_%d.jpg' % img_c, o1)
        print("Saved calib images %d" % img_c)
        img_c += 1
        btn_cl = False

    c.imshow("Duo", cm)
    k = c.waitKey(1) & 0xFF
    if k == ord('q'): break
    elif k == ord('4'): 
        c0, c1 = c1, c0
        idx0, idx1 = idx1, idx0
    elif k == ord('3'): cam_mode = (cam_mode + 1) % 3
    elif k == ord('1'): 
        rot0 = (rot0 + 1) % 4
        save_rot()
    elif k == ord('2'): 
        rot1 = (rot1 + 1) % 4
        save_rot()

a = False
c0.release()
c1.release()
c.destroyAllWindows()
d.close()
