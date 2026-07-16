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
import json
import ui
import time


idx0 = 0
c0 = c.VideoCapture(idx0)

o = v.HandLandmarkerOptions(
    base_options=p.BaseOptions(model_asset_path='hand_landmarker.task'),
    running_mode=v.RunningMode.IMAGE,
    num_hands=2
)
d = v.HandLandmarker.create_from_options(o)

with open('components_10.json','r') as f:
    COMPONENTS=json.load(f)
    print("Loaded", len(COMPONENTS), "components")
print(COMPONENTS["esp32"])
prev=time.time()
cn = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(17,18),(18,19),(19,20),(0,17)]

bd0 = []
cf0 = None
a = True

def wk():
    global bd0
    s = r.Session()
    u = 'https://detect.roboflow.com/find-battery-current-vzeoc/2'
    q = {'api_key': '84aau744LSxt5mDCmfY4'}
    while a:
        cf = cf0
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
                bd0 = nb
            except Exception as e:
                print(f"API Error:", e)
        import time
        time.sleep(0.2)

t.Thread(target=wk, daemon=True).start()

import os, json
rot_file = 'rot_config.json'
if os.path.exists(rot_file):
    with open(rot_file, 'r') as f:
        cfg = json.load(f)
        rot0 = cfg.get('rot0', 0)
else:
    rot0 = 0

def save_rot():
    with open(rot_file, 'w') as f: json.dump({'rot0': rot0}, f)

img_c = 0
btn_cl = False
cam_mode = 0
def m_cb(e, x, y, f, p):
    global btn_cl
    if e == c.EVENT_LBUTTONDOWN and 10 <= x <= 160 and 10 <= y <= 60: btn_cl = True
c.namedWindow("Mono")
c.setMouseCallback("Mono", m_cb)

def fingers_up(hand, handedness):
    up = []

    # Thumb
    if handedness == "Right":
        up.append(hand[4].x < hand[3].x)
    else:
        up.append(hand[4].x > hand[3].x)

    # Index
    up.append(hand[8].y < hand[6].y)

    # Middle
    up.append(hand[12].y < hand[10].y)

    # Ring
    up.append(hand[16].y < hand[14].y)

    # Pinky
    up.append(hand[20].y < hand[18].y)

    return up

organising = False
last_gesture = 0
organising_until = 0

peace_sign = [True, True, True, False, False]  
devil_sign = [True, True, False, False, True]
yolo_sign = [False, False, False, False, True]
flip_off_sign = [False, False, True, False, False]

while True:
    ok0, r0 = c0.read()
    
    if not ok0 or r0 is None:
        r0 = n.zeros((480, 640, 3), dtype=n.uint8)
        c.putText(r0, "NO CAM %d" % idx0, (50, 240), c.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
    
    if rot0 == 1: r0 = c.rotate(r0, c.ROTATE_90_CLOCKWISE)
    elif rot0 == 2: r0 = c.rotate(r0, c.ROTATE_180)
    elif rot0 == 3: r0 = c.rotate(r0, c.ROTATE_90_COUNTERCLOCKWISE)
    
    o0 = r0.copy()
    
    f0 = c.resize(r0, (int(480 * r0.shape[1] / r0.shape[0]), 480))
    cf0 = f0.copy()
    f0_h, f0_w = f0.shape[:2]
    
    for x1, y1, x2, y2, lb, co in bd0:
        c.rectangle(f0, (x1, y1), (x2, y2), (0, 255, 0), 2)
        c.putText(f0, "%s %.2f" % (lb, co), (x1, y1 - 10), c.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
    r0 = c.cvtColor(f0, c.COLOR_BGR2RGB)
    
    pt0 = None
    
    hr0 = d.detect(m.Image(image_format=m.ImageFormat.SRGB, data=r0))
    if hr0.hand_landmarks:
        h0 = hr0.hand_landmarks[0]
        handedness = hr0.handedness[0][0].category_name
        f = fingers_up(h0, handedness)
        if f == peace_sign:
            now = time.time()

            if now - last_gesture > 2:
                print("Organising Desk")
                organising = True
                organising_until = now + 3      # Show banner for 3 seconds
                last_gesture = now
        if f == devil_sign:
            print("Devil Sign Detected")
        if f == yolo_sign:
            print("YOLO Sign Detected")
        if f == flip_off_sign:
            print("Flip Off Sign Detected")
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
        selected_component=p_obj if p_obj!='None' else None

    cm = f0
    c.rectangle(cm, (10, 10), (160, 60), (0, 0, 255), -1)
    c.putText(cm, "CAPTURE", (25, 45), c.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    c.putText(cm, "Captured: %d" % img_c, (10, 90), c.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    now = time.time()
    fps = 1.0 / max(now - prev, 1e-6)
    prev = now

    if time.time() > organising_until:
        organising = False
    

    try:
        cm = ui.draw(
            f0,
            bd0,
            hr0.hand_landmarks if hr0.hand_landmarks else [],
            cn,
            selected_component if 'selected_component' in locals() else None,
            COMPONENTS,
            fps,
            "AI Ready",
            f"Objects: {len(bd0)}",
            organising
        )
    except Exception as e:
        print(e)

    if btn_cl:
        import os
        if not os.path.exists('calib'): os.makedirs('calib')
        c.imwrite('calib/t_%d.jpg' % img_c, o0)
        print("Saved calib image %d" % img_c)
        img_c += 1
        btn_cl = False

    c.imshow("Mono", cm)
    k = c.waitKey(1) & 0xFF
    if k == ord('q'): break
    elif k == ord('5'):
        c0.release()
        idx0 = (idx0 + 1) % 5
        c0 = c.VideoCapture(idx0)
    elif k == ord('1'): 
        rot0 = (rot0 + 1) % 4
        save_rot()

a = False
c0.release()
c.destroyAllWindows()
d.close()