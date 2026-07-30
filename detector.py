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
import overlay as ov
import shutil
import wave
import queue

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_FILENAME = "temp.wav"

class AudioRecorder:
    def __init__(self, filename=AUDIO_FILENAME, samplerate=AUDIO_SAMPLE_RATE, channels=AUDIO_CHANNELS):
        self.filename = filename
        self.samplerate = samplerate
        self.channels = channels
        self.buffer = queue.Queue()
        self._stop_event = t.Event()
        self.stream = None
        self.thread = None

    def _callback(self, indata, frames, time_info, status):
        if status:
            pass
        self.buffer.put(indata.copy())

    def _writer(self):
        with wave.open(self.filename, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.samplerate)
            while not self._stop_event.is_set() or not self.buffer.empty():
                try:
                    data = self.buffer.get(timeout=0.1)
                except queue.Empty:
                    continue
                wf.writeframes(data.tobytes())

    def start(self):
        if self.thread is not None:
            return
        self._stop_event.clear()
        self.thread = t.Thread(target=self._writer, daemon=True)
        self.thread.start()
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype="int16",
            callback=self._callback
        )
        self.stream.start()

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self._stop_event.set()
        if self.thread is not None:
            self.thread.join()
            self.thread = None

ov.start()
ov.generate_and_display_markers()
active_box_ids = set()

dict_aruco = c.aruco.getPredefinedDictionary(c.aruco.DICT_4X4_50)
params_aruco = c.aruco.DetectorParameters()
detector_aruco = c.aruco.ArucoDetector(dict_aruco, params_aruco)

idx0 = 0
idx1 = 2
c0 = c.VideoCapture(idx0)
c1 = c.VideoCapture(idx1)

try:
    st = n.load("stereo.npz")
    p0 = st["P0"]
    p1 = st["P1"]
except:
    pass
    p0, p1 = None, None

o = v.HandLandmarkerOptions(
    base_options=p.BaseOptions(model_asset_path='hand_landmarker.task'),
    running_mode=v.RunningMode.IMAGE,
    num_hands=2,
    min_hand_detection_confidence=0.50,
    min_hand_presence_confidence=0.50,
    min_tracking_confidence=0.50
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
    from ultralytics import YOLO
    import torch
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    model = None
    loaded_path = None
    
    last_gray = None
    tracks = []
    
    def get_iou(bb1, bb2):
        assert bb1[0] < bb1[2]
        assert bb1[1] < bb1[3]
        assert bb2[0] < bb2[2]
        assert bb2[1] < bb2[3]
        x_left = max(bb1[0], bb2[0])
        y_top = max(bb1[1], bb2[1])
        x_right = min(bb1[2], bb2[2])
        y_bottom = min(bb1[3], bb2[3])
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        bb1_area = (bb1[2] - bb1[0]) * (bb1[3] - bb1[1])
        bb2_area = (bb2[2] - bb2[0]) * (bb2[3] - bb2[1])
        iou = intersection_area / float(bb1_area + bb2_area - intersection_area)
        return iou

    while a:
        target_path = 'battery_model.pt' if os.path.exists('battery_model.pt') else 'yolo11n.pt'
        if model is None or loaded_path != target_path:
            try:
                pass
                model = YOLO(target_path)
                loaded_path = target_path
            except Exception as e:
                pass
                time.sleep(2.0)
                continue

        cf = cf0 if cam_id == 0 else cf1
        if cf is not None and model is not None:
            try:
                cs = cf.copy()
                gray = c.cvtColor(cs, c.COLOR_BGR2GRAY)
                if last_gray is None or last_gray.shape != gray.shape:
                    last_gray = gray
                diff = c.absdiff(gray, last_gray)
                last_gray = gray
                
                results = model(cs, imgsz=320, conf=0.30, device=device, verbose=False)[0]
                
                raw_dets = []
                for box in results.boxes:
                    conf = float(box.conf[0])
                    if conf > 0.30:
                        cls_id = int(box.cls[0])
                        cls_name = model.names[cls_id]
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        if cls_name == 'arduino_uno':
                            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                            w, h = (x2 - x1) * 0.80, (y2 - y1) * 0.80
                            x1, x2 = int(cx - w/2), int(cx + w/2)
                            y1, y2 = int(cy - h/2), int(cy + h/2)
                        raw_dets.append((x1, y1, x2, y2, cls_name, conf))
                
                new_tracks = []
                for det in raw_dets:
                    dx1, dy1, dx2, dy2, dcls, dconf = det
                    best_idx = -1
                    best_iou = 0.2
                    for i, t in enumerate(tracks):
                        if t[4] == dcls:
                            iou = get_iou((dx1, dy1, dx2, dy2), (t[0], t[1], t[2], t[3]))
                            if iou > best_iou:
                                best_iou = iou
                                best_idx = i
                    if best_idx >= 0:
                        t = tracks.pop(best_idx)
                        dcx, dcy = (dx1 + dx2) / 2.0, (dy1 + dy2) / 2.0
                        tcx, tcy = (t[0] + t[2]) / 2.0, (t[1] + t[3]) / 2.0
                        dw, dh = dx2 - dx1, dy2 - dy1
                        tw, th = t[2] - t[0], t[3] - t[1]
                        
                        scx = 0.7 * dcx + 0.3 * tcx
                        scy = 0.7 * dcy + 0.3 * tcy
                        
                        sw = 0.10 * dw + 0.90 * tw
                        sh = 0.10 * dh + 0.90 * th
                        
                        sx1 = int(scx - sw/2)
                        sy1 = int(scy - sh/2)
                        sx2 = int(scx + sw/2)
                        sy2 = int(scy + sh/2)
                        new_tracks.append((sx1, sy1, sx2, sy2, dcls, dconf, 0))
                    else:
                        new_tracks.append((dx1, dy1, dx2, dy2, dcls, dconf, 0))
                
                h_img, w_img = cs.shape[:2]
                for t in tracks:
                    tx1, ty1 = max(0, t[0]), max(0, t[1])
                    tx2, ty2 = min(w_img, t[2]), min(h_img, t[3])
                    motion = 0
                    if tx2 > tx1 and ty2 > ty1:
                        motion = diff[ty1:ty2, tx1:tx2].mean()
                    
                    age = t[6] + 1
                    if motion < 15 and age < 100:
                        new_tracks.append((t[0], t[1], t[2], t[3], t[4], t[5], age))
                
                tracks = new_tracks
                nb = [(t[0], t[1], t[2], t[3], t[4], t[5]) for t in tracks]
                
                if cam_id == 0: bd0 = nb
                else: bd1 = nb
            except Exception as e:
                pass
        time.sleep(0.05)

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
        
        corners, ids, rejected = detector_aruco.detectMarkers(f0)
        c.aruco.drawDetectedMarkers(f0, corners, ids)
        
        H = getattr(ov, 'last_H', None)
        if ids is not None and len(ids) >= 4:
            src_pts = []
            dst_pts = []
            norm_corners_dict = ov.get_marker_normalized_corners()
            for i in range(len(ids)):
                marker_id = ids[i][0]
                if marker_id in norm_corners_dict:
                    src_pts.extend(corners[i][0])
                    dst_pts.extend(norm_corners_dict[marker_id])
            if len(src_pts) >= 16:
                src_pts = n.array(src_pts, dtype=n.float32)
                dst_pts = n.array(dst_pts, dtype=n.float32)
                new_H, _ = c.findHomography(src_pts, dst_pts)
                if new_H is not None:
                    H = new_H
                    ov.last_H = H
                    for i_idx, i_val in enumerate(ids):
                        if i_val[0] == 0:
                            ov.anchor_pos = n.mean(corners[i_idx][0], axis=0)
                            break
                    if not getattr(ov, 'calibrated_once', False):
                        ov.calib_counter = getattr(ov, 'calib_counter', 0) + 1
                        if ov.calib_counter % 15 == 0:
                            pass
                        if ov.calib_counter >= 45:
                            ov.hide_calibration_markers(keep_anchor=True)
                            ov.calibrated_once = True
                            pass
        else:
            if ids is not None and getattr(ov, 'anchor_pos', None) is not None:
                for i_idx, i_val in enumerate(ids):
                    if i_val[0] == 0:
                        curr_pos = n.mean(corners[i_idx][0], axis=0)
                        dist = n.linalg.norm(curr_pos - ov.anchor_pos)
                        if dist > 30:
                            pass
                            ov.generate_and_display_markers()
                            ov.calibrated_once = False
                            ov.calib_counter = 0
                            ov.last_H = None
                            H = None
                        break
        
        new_active = set()
        
        target_zone = (350, 150, 500, 300)
        target_color_hex = "#ff0000"
        
        for i, (x1, y1, x2, y2, lb, co) in enumerate(bd0):
            if lb == 'arduino_uno':
                cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                if target_zone[0] <= cx <= target_zone[2] and target_zone[1] <= cy <= target_zone[3]:
                    target_color_hex = "#00ff00"
                    break
        
        if H is not None:
            target_ar_cx = target_ar_cy = None
            t_pts = n.array([[[target_zone[0], target_zone[1]]], [[target_zone[2], target_zone[1]]], [[target_zone[2], target_zone[3]]], [[target_zone[0], target_zone[3]]]], dtype=n.float32)
            t_dst = c.perspectiveTransform(t_pts, H)
            if t_dst is not None:
                tnx1, tny1 = float(n.min(t_dst[:, 0, 0])), float(n.min(t_dst[:, 0, 1]))
                tnx2, tny2 = float(n.max(t_dst[:, 0, 0])), float(n.max(t_dst[:, 0, 1]))
                target_ar_cx, target_ar_cy = (tnx1 + tnx2) / 2.0, (tny1 + tny2) / 2.0
                new_active.add("ar_target_zone")
                ov.highlight_bbox((tnx1, tny1, tnx2, tny2), label="Place Arduino Here", id_="ar_target_zone", color=target_color_hex, layer=0, animation="none")

            for i, (x1, y1, x2, y2, lb, co) in enumerate(bd0):
                ar_y1, ar_y2 = y1, y2
                if lb == 'arduino_uno':
                    y_offset = int((y2 - y1) * 0.18)
                    ar_y1 += y_offset
                    ar_y2 += y_offset
                
                pts = n.array([[[x1, ar_y1]], [[x2, ar_y1]], [[x2, ar_y2]], [[x1, ar_y2]]], dtype=n.float32)
                dst = c.perspectiveTransform(pts, H)
                if dst is not None:
                    nx1, ny1 = float(n.min(dst[:, 0, 0])), float(n.min(dst[:, 0, 1]))
                    nx2, ny2 = float(n.max(dst[:, 0, 0])), float(n.max(dst[:, 0, 1]))
                    box_id = f"ar_box_{i}"
                    new_active.add(box_id)
                    ov.highlight_bbox((nx1, ny1, nx2, ny2), label=lb, id_=box_id, color="#00ff00", layer=1, animation="pulse")
                    
                    if lb == 'arduino_uno' and target_ar_cx is not None:
                        acx, acy = (nx1 + nx2) / 2.0, (ny1 + ny2) / 2.0
                        new_active.add("arduino_guidance_arrow")
                        ov.draw_arrow((acx, acy), (target_ar_cx, target_ar_cy), id_="arduino_guidance_arrow", color=target_color_hex, layer=2, animation="flow")
        
        for old_id in active_box_ids - new_active:
            ov.remove(old_id)
        active_box_ids = new_active

        if hr0.hand_landmarks:
            h0 = hr0.hand_landmarks[0]
            handedness = hr0.handedness[0][0].category_name
            f_up = fingers_up(h0, handedness)
            
            if f_up == peace_sign:
                now = time.time()
                if now - last_gesture > 2:
                    pass
                    organising = True
                    organising_until = now + 3
                    last_gesture = now
            elif f_up == devil_sign:
                pass
            
            ui.draw_hand(f0, [h0], cn)
            tip_x = h0[8].x + 0.35 * (h0[8].x - h0[7].x)
            tip_y = h0[8].y + 0.35 * (h0[8].y - h0[7].y)
            pt0 = (int(tip_x * f0_w), int(tip_y * f0_h))
            c.circle(f0, pt0, 6, (255, 255, 0), -1)
        
            if H is not None and pt0:
                f_pts = n.array([[[pt0[0], pt0[1]]]], dtype=n.float32)
                f_dst = c.perspectiveTransform(f_pts, H)
                if f_dst is not None:
                    fnx, fny = float(f_dst[0][0][0]), float(f_dst[0][0][1])
                    pass
                    ov.draw_crosshair(fnx, fny, size=0.05, id_="ar_finger", color="#00ffff", layer=4, animation="glow", thickness=3)
            else:
                ov.remove("ar_finger")
                
            p_obj = 'None'
            for bx1, by1, bx2, by2, lb, co in bd0:
                if bx1 <= pt0[0] <= bx2 and by1 <= pt0[1] <= by2:
                    p_obj = lb
                    break
            selected_component = p_obj if p_obj != 'None' else None

    if cam_mode in [0, 2]:
        hr1 = d.detect(m.Image(image_format=m.ImageFormat.SRGB, data=r1_rgb))
        if hr1.hand_landmarks:
            ui.draw_hand(f1, [h1], cn)
            tip_x1 = h1[8].x + 0.35 * (h1[8].x - h1[7].x)
            tip_y1 = h1[8].y + 0.35 * (h1[8].y - h1[7].y)
            pt1 = (int(tip_x1 * f1_w), int(tip_y1 * f1_h))
            c.circle(f1, pt1, 6, (255, 255, 0), -1)
            
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
    elif k == ord('k'):
        pass
        ov.generate_and_display_markers()
        ov.calibrated_once = False
        ov.calib_counter = 0
        ov.last_H = None
        H = None
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
            if shutil.which("rec") is not None:
                is_recording_v = True
                rec_proc = subprocess.Popen(["rec", "-r", "16000", "-c", "1", "-b", "16", "temp.wav", "-q"])
            elif SOUNDDEVICE_AVAILABLE:
                is_recording_v = True
                rec_proc = AudioRecorder(AUDIO_FILENAME, AUDIO_SAMPLE_RATE, AUDIO_CHANNELS)
                rec_proc.start()
            else:
                pass
        elif is_recording_v:
            is_recording_v = False
            if rec_proc:
                if isinstance(rec_proc, AudioRecorder):
                    rec_proc.stop()
                else:
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
            if shutil.which("rec") is not None:
                is_recording_t = True
                rec_proc = subprocess.Popen(["rec", "-r", "16000", "-c", "1", "-b", "16", "temp.wav", "-q"])
            elif SOUNDDEVICE_AVAILABLE:
                is_recording_t = True
                rec_proc = AudioRecorder(AUDIO_FILENAME, AUDIO_SAMPLE_RATE, AUDIO_CHANNELS)
                rec_proc.start()
            else:
                pass
        elif is_recording_t:
            is_recording_t = False
            if rec_proc:
                if isinstance(rec_proc, AudioRecorder):
                    rec_proc.stop()
                else:
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
