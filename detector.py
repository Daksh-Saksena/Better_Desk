import cv2 as c
import numpy as n
from mediapipe.tasks import python as p
from mediapipe.tasks.python import vision as v
import mediapipe as m
import sys as y
import threading as t
import base64 as b
import requests as r
import os
import json
import time
import ui
import voice_agent
import subprocess

idx0 = 0
idx1 = 2
c0 = c.VideoCapture(idx0)
c1 = c.VideoCapture(idx1)

try:
    st = n.load("stereo.npz")
    p0 = st["P0"]
    p1 = st["P1"]
except:
    print("WARNING: stereo.npz not found! 3D tracking disabled.")
    p0, p1 = None, None

o = v.HandLandmarkerOptions(
    base_options=p.BaseOptions(model_asset_path='hand_landmarker.task'),
    running_mode=v.RunningMode.IMAGE,
    num_hands=2
)
d = v.HandLandmarker.create_from_options(o)
cn = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(17,18),(18,19),(19,20),(0,17)]

with open('components_10.json','r') as f:
    COMPONENTS=json.load(f)

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
                pass
        time.sleep(0.2)

t.Thread(target=wk, args=(0,), daemon=True).start()
t.Thread(target=wk, args=(1,), daemon=True).start()

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

cam_mode = 1
prev = time.time()
ai_status = "AI Ready"
ai_busy = False
is_recording_v = False
is_recording_t = False
rec_proc = None

def fingers_up(hand, handedness):
    up = []
    # Thumb
    if handedness == "Right": up.append(hand[4].x < hand[3].x)
    else: up.append(hand[4].x > hand[3].x)
    # Index, Middle, Ring, Pinky
    up.append(hand[8].y < hand[6].y)
    up.append(hand[12].y < hand[10].y)
    up.append(hand[16].y < hand[14].y)
    up.append(hand[20].y < hand[18].y)
    return up

organising = False
last_gesture = 0
organising_until = 0

peace_sign = [True, True, True, False, False]  
devil_sign = [True, True, False, False, True]
yolo_sign = [False, False, False, False, True]
flip_off_sign = [False, False, True, False, False]

c.namedWindow("BetterDesk", c.WINDOW_NORMAL)

while True:
    ok0, r0 = c0.read()
    if cam_mode in [0, 2]:
        ok1, r1 = c1.read()
    else:
        ok1, r1 = False, None
    
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
    
    r0_rgb = c.cvtColor(f0, c.COLOR_BGR2RGB)
    r1_rgb = c.cvtColor(f1, c.COLOR_BGR2RGB)
    
    pt0 = None
    pt1 = None
    selected_component = None
    
    if cam_mode in [0, 1]:
        hr0 = d.detect(m.Image(image_format=m.ImageFormat.SRGB, data=r0_rgb))
        if hr0.hand_landmarks:
            h0 = hr0.hand_landmarks[0]
            handedness = hr0.handedness[0][0].category_name
            f_up = fingers_up(h0, handedness)
            
            if f_up == peace_sign:
                now = time.time()
                if now - last_gesture > 2:
                    print("Peace Sign -> Organising Desk")
                    organising = True
                    organising_until = now + 3
                    last_gesture = now
            elif f_up == devil_sign:
                pass
            
            ui.draw_hand(f0, [h0], cn)
            pt0 = (int(h0[8].x * f0_w), int(h0[8].y * f0_h))
            
            p_obj = 'None'
            for bx1, by1, bx2, by2, lb, co in bd0:
                if bx1 <= pt0[0] <= bx2 and by1 <= pt0[1] <= by2:
                    p_obj = lb
                    break
            selected_component = p_obj if p_obj != 'None' else None

    if cam_mode in [0, 2]:
        hr1 = d.detect(m.Image(image_format=m.ImageFormat.SRGB, data=r1_rgb))
        if hr1.hand_landmarks:
            h1 = hr1.hand_landmarks[0]
            ui.draw_hand(f1, [h1], cn)
            pt1 = (int(h1[8].x * f1_w), int(h1[8].y * f1_h))
            
            p_obj1 = 'None'
            for bx1, by1, bx2, by2, lb, co in bd1:
                if bx1 <= pt1[0] <= bx2 and by1 <= pt1[1] <= by2:
                    p_obj1 = lb
                    break
            if selected_component is None and p_obj1 != 'None':
                selected_component = p_obj1

    ui.draw_boxes(f0, bd0, selected_component)
    ui.draw_boxes(f1, bd1, selected_component)

    lx, ly, lz = None, None, None
    if cam_mode == 0 and pt0 and pt1 and p0 is not None and p1 is not None:
        pts = c.triangulatePoints(p0, p1, n.array([[pt0[0]], [pt0[1]]], dtype=n.float32), n.array([[pt1[0]], [pt1[1]]], dtype=n.float32))
        pts /= pts[3]
        lx, ly, lz = pts[0, 0], pts[1, 0], pts[2, 0]

    if cam_mode == 0:
        cm = c.hconcat([f0, f1])
    elif cam_mode == 1:
        cm = f0
    elif cam_mode == 2:
        cm = f1

    now = time.time()
    fps = 1.0 / max(now - prev, 1e-6)
    prev = now
    
    if time.time() > organising_until:
        organising = False
    
    bottom_str = f"3D Coord: X={lx:.1f} Y={ly:.1f} Z={lz:.1f}" if lx else "Ready"
    cm = ui.draw_dashboard(cm, selected_component, COMPONENTS, fps, ai_status, bottom_str, organising)

    if is_recording_v or is_recording_t:
        _h, _w = cm.shape[:2]
        c.circle(cm, (_w - 190, 25), 8, (0, 0, 255), -1)
        c.putText(cm, "RECORDING MIC", (_w - 170, 30), c.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    c.imshow("BetterDesk", cm)
    k = c.waitKey(1) & 0xFF
    if k == ord('q'): break
    elif k == ord(' '):
        if not ai_busy and not is_recording_v and not is_recording_t:
            snap = cm.copy()
            ai_busy = True
            ai_status = "Analysing..."
            def _done(txt):
                global ai_busy, ai_status
                ai_busy = False
                ai_status = "AI Ready"
            voice_agent.analyse_and_speak(frame_bgr=snap, audio_file=None, on_done=_done)
    elif k == ord('v'):
        if not is_recording_v and not ai_busy:
            is_recording_v = True
            rec_proc = subprocess.Popen(["rec", "-r", "16000", "-c", "1", "-b", "16", "temp.wav", "-q"])
        elif is_recording_v:
            is_recording_v = False
            if rec_proc:
                rec_proc.terminate()
                rec_proc.wait()
            snap = cm.copy()
            ai_busy = True
            ai_status = "Analysing..."
            def _done(txt):
                global ai_busy, ai_status
                ai_busy = False
                ai_status = "AI Ready"
            voice_agent.analyse_and_speak(frame_bgr=snap, audio_file="temp.wav", on_done=_done)
    elif k == ord('t'):
        if not is_recording_t and not ai_busy:
            is_recording_t = True
            rec_proc = subprocess.Popen(["rec", "-r", "16000", "-c", "1", "-b", "16", "temp.wav", "-q"])
        elif is_recording_t:
            is_recording_t = False
            if rec_proc:
                rec_proc.terminate()
                rec_proc.wait()
            ai_busy = True
            ai_status = "Analysing..."
            def _done(txt):
                global ai_busy, ai_status
                ai_busy = False
                ai_status = "AI Ready"
            voice_agent.analyse_and_speak(frame_bgr=None, audio_file="temp.wav", on_done=_done)
    elif k == ord('4'): 
        c0, c1 = c1, c0
        idx0, idx1 = idx1, idx0
    elif k == ord('3'): cam_mode = (cam_mode + 1) % 3
    elif k == ord('5'):
        c0.release()
        idx0 = (idx0 + 1) % 5
        c0 = c.VideoCapture(idx0)
    elif k == ord('6'):
        c1.release()
        idx1 = (idx1 + 1) % 5
        c1 = c.VideoCapture(idx1)
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
