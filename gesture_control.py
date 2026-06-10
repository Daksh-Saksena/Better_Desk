import cv2
import mediapipe as mp
import pyautogui
import math
import time
import sys

cam_id = 0
if len(sys.argv) > 1 and sys.argv[1].isdigit():
    cam_id = int(sys.argv[1])
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.0

swap_xy = True
flip_x = True
flip_y = True
x0, x1 = 0.15, 0.85
y0, y1 = 0.15, 0.85
alpha = 0.25
use_dyn = True
a_min, a_max = 0.15, 0.75
dead_zone = 0.5
ramp = 80.0
left_th = 0.045
left_rel = 0.060
scroll_th = 15
scroll_mul = 0.5
inv_scroll = False

def dist2d(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)
def dist3d(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)
def is_ext(hand, tip, mcp):
    w = hand.landmark[0]
    t = hand.landmark[tip]
    m = hand.landmark[mcp]
    return dist3d(t, w) > dist3d(m, w) * 1.15
def norm(val, v_min, v_max):
    val = max(v_min, min(v_max, val))
    return (val - v_min) / (v_max - v_min)
cap = cv2.VideoCapture(cam_id)
ok, _ = cap.read()
if not cap.isOpened() or not ok:
    fb = 1 if cam_id == 0 else 0
    cap.release()
    cap = cv2.VideoCapture(fb)
    ok, _ = cap.read()
    if not cap.isOpened() or not ok:
        sys.exit(1)
    cam_id = fb
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
mp_h = mp.solutions.hands
mp_d = mp.solutions.drawing_utils
hands = mp_h.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

w, h = pyautogui.size()
prev_x, prev_y = w // 2, h // 2
lp = False
sc = False
sc_y0 = 0.0
t0 = time.time()
last_rel = 0.0

while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(frame, 1)
    fh, fw, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)
    act = "IDLE"
    pinch = "N/A"
    if res.multi_hand_landmarks:
        hand = res.multi_hand_landmarks[0]
        mp_d.draw_landmarks(frame, hand, mp_h.HAND_CONNECTIONS)
        idx = is_ext(hand, 8, 5)
        mid = is_ext(hand, 12, 9)
        ring = is_ext(hand, 16, 13)
        pink = is_ext(hand, 20, 17)
        tip = hand.landmark[8]
        tx = norm(tip.x, x0, x1)
        ty = norm(tip.y, y0, y1)
        if swap_xy:
            tx, ty = ty, tx
        if flip_x:
            tx = 1.0 - tx
        if flip_y:
            ty = 1.0 - ty
        tx = max(0, min(w - 1, int(tx * w)))
        ty = max(0, min(h - 1, int(ty * h)))
        if use_dyn:
            dist = math.hypot(tx - prev_x, ty - prev_y)
            if dist < dead_zone:
                sx, sy = prev_x, prev_y
            else:
                a = a_min + (a_max - a_min) * min(1.0, (dist - dead_zone) / ramp)
                sx = int(a * tx + (1.0 - a) * prev_x)
                sy = int(a * ty + (1.0 - a) * prev_y)
        else:
            sx = int(alpha * tx + (1.0 - alpha) * prev_x)
            sy = int(alpha * ty + (1.0 - alpha) * prev_y)
        cv2.circle(frame, (int(tip.x * fw), int(tip.y * fh)), 12, (0, 255, 0), -1)
        if idx and mid and not ring and not pink:
            act = "SCROLL"
            if not sc:
                sc = True
                sc_y0 = sy
            else:
                dy = sy - sc_y0
                if abs(dy) > scroll_th:
                    ticks = int(-dy * scroll_mul)
                    if inv_scroll:
                        ticks = -ticks
                    if ticks != 0:
                        pyautogui.scroll(ticks)
                        sc_y0 = sy
        else:
            sc = False
        if not sc:
            pyautogui.moveTo(sx, sy)
            act = "MOVE"
            prev_x, prev_y = sx, sy
            pinch_dist = dist2d(hand.landmark[4], hand.landmark[8])
            pinch = f"L: {pinch_dist:.3f}"
            if not lp and pinch_dist < left_th:
                lp = True
                pyautogui.mouseDown()
            elif lp and pinch_dist > left_rel:
                lp = False
                pyautogui.mouseUp()
                last_rel = time.time()
            if lp:
                act = "DRAG" if (time.time() - last_rel > 0.4) else "HOLD"
    else:
        act = "NO HAND"
        if lp:
            pyautogui.mouseUp()
            lp = False
    now = time.time()
    fps = 1.0 / (now - t0)
    t0 = now
    cv2.rectangle(frame, (10, 10), (320, 130), (0, 128, 0), -1)
    cv2.rectangle(frame, (10, 10), (320, 130), (255, 255, 255), 2)
    cv2.putText(frame, "STATUS: ACTIVE", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"ACTION: {act}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"PINCH: {pinch}", (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.imshow("BetterDesk Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
if lp:
    pyautogui.mouseUp()
cap.release()
cv2.destroyAllWindows()