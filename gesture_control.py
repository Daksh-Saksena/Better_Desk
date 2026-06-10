import cv2
import mediapipe as mp
import pyautogui
import math
import time
import sys

cam_id = 0
if len(sys.argv) > 1 and sys.argv[1].isdigit():
    cam_id = int(sys.argv[1])

real_mouse = False

left_th = 0.045
left_rel = 0.060
scroll_th = 15
scroll_mul = 0.5
inv_scroll = False

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

acc_th = 5.0
acc_gain = 0.05
acc_max = 3.0

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
prev_tx, prev_ty = w // 2, h // 2
hand_active = False

lp = False
sc = False
sc_y0 = 0.0
t0 = time.time()
last_rel = 0.0

lock_x, lock_y = 0, 0
lock_tx, lock_ty = 0, 0
lock_broken = False

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
    v = 0.0
    a = alpha
    acc = 1.0

    if res.multi_hand_landmarks:
        hand = res.multi_hand_landmarks[0]
        mp_d.draw_landmarks(frame, hand, mp_h.HAND_CONNECTIONS)

        tip = hand.landmark[8]
        in_zone = x0 <= tip.x <= x1 and y0 <= tip.y <= y1

        if in_zone:
            idx = is_ext(hand, 8, 5)
            mid = is_ext(hand, 12, 9)
            ring = is_ext(hand, 16, 13)
            pink = is_ext(hand, 20, 17)

            tx = norm(tip.x, x0, x1)
            ty = norm(tip.y, y0, y1)

            if swap_xy:
                tx, ty = ty, tx
            if flip_x:
                tx = 1.0 - tx
            if flip_y:
                ty = 1.0 - ty

            tx_raw = max(2, min(w - 3, int(tx * w)))
            ty_raw = max(2, min(h - 3, int(ty * h)))

            if not hand_active:
                prev_x, prev_y = tx_raw, ty_raw
                prev_tx, prev_ty = tx_raw, ty_raw
                hand_active = True

            dx = tx_raw - prev_tx
            dy = ty_raw - prev_ty
            v = math.hypot(dx, dy)

            if v > acc_th:
                acc = min(acc_max, 1.0 + (v - acc_th) * acc_gain)

            ax = prev_x + dx * acc
            ay = prev_y + dy * acc

            ax = max(2, min(w - 3, int(ax)))
            ay = max(2, min(h - 3, int(ay)))

            if use_dyn:
                if v < dead_zone:
                    sx, sy = prev_x, prev_y
                    a = 0.0
                else:
                    a = a_min + (a_max - a_min) * min(1.0, (v - dead_zone) / ramp)
                    sx = int(a * ax + (1.0 - a) * prev_x)
                    sy = int(a * ay + (1.0 - a) * prev_y)
            else:
                sx = int(alpha * ax + (1.0 - alpha) * prev_x)
                sy = int(alpha * ay + (1.0 - alpha) * prev_y)

            cv2.circle(frame, (int(tip.x * fw), int(tip.y * fh)), 12, (0, 255, 0), -1)

            idx_mid_d = dist2d(hand.landmark[8], hand.landmark[12])
            if idx and mid and not ring and not pink and idx_mid_d < left_th:
                act = "SCROLL"
                if not sc:
                    sc = True
                    sc_y0 = sy
                else:
                    s_dy = sy - sc_y0
                    if abs(s_dy) > scroll_th:
                        ticks = int(-s_dy * scroll_mul)
                        if inv_scroll:
                            ticks = -ticks
                        if ticks != 0:
                            if real_mouse:
                                pyautogui.scroll(ticks)
                            sc_y0 = sy
            else:
                sc = False

            if not sc:
                d_thumb_idx = dist2d(hand.landmark[4], hand.landmark[8])
                d_thumb_mid = dist2d(hand.landmark[4], hand.landmark[12])
                pinch = f"L:{d_thumb_idx:.3f}/{left_th:.3f} M:{d_thumb_mid:.3f}"

                if not lp and d_thumb_idx < left_th:
                    lp = True
                    lock_x, lock_y = prev_x, prev_y
                    lock_tx, lock_ty = tx_raw, ty_raw
                    if d_thumb_mid < left_th:
                        lock_broken = True
                    else:
                        lock_broken = False
                    if real_mouse:
                        pyautogui.mouseDown()
                elif lp and d_thumb_idx > left_rel:
                    lp = False
                    lock_broken = False
                    if real_mouse:
                        pyautogui.mouseUp()
                    last_rel = time.time()

                if lp:
                    if lock_broken:
                        if real_mouse:
                            pyautogui.moveTo(sx, sy)
                        act = "DRAG"
                        prev_x, prev_y = sx, sy
                        prev_tx, prev_ty = tx_raw, ty_raw
                    else:
                        if real_mouse:
                            pyautogui.moveTo(lock_x, lock_y)
                        act = "LOCKED"
                        prev_x, prev_y = lock_x, lock_y
                else:
                    if real_mouse:
                        pyautogui.moveTo(sx, sy)
                    act = "MOVE"
                    prev_x, prev_y = sx, sy
                    prev_tx, prev_ty = tx_raw, ty_raw
        else:
            act = "OUT OF ZONE"
            hand_active = False
            if lp:
                if real_mouse:
                    pyautogui.mouseUp()
                lp = False
    else:
        act = "NO HAND"
        hand_active = False
        if lp:
            if real_mouse:
                pyautogui.mouseUp()
            lp = False

    now = time.time()
    fps = 1.0 / (now - t0)
    t0 = now

    cv2.rectangle(frame, (10, 10), (320, 210), (0, 128, 0), -1)
    cv2.rectangle(frame, (10, 10), (320, 210), (255, 255, 255), 2)

    ix0, ix1 = int(x0 * fw), int(x1 * fw)
    iy0, iy1 = int(y0 * fh), int(y1 * fh)
    cv2.rectangle(frame, (ix0, iy0), (ix1, iy1), (255, 255, 255), 2)

    cv2.putText(frame, "STATUS: ACTIVE", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"ACTION: {act}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"PINCH: {pinch}", (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, f"VEL: {v:.1f}", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, f"SMOOTH: {a:.2f}", (20, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, f"ACCEL: {acc:.2f}", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    if act == "LOCKED":
        cv2.putText(frame, "LOCKED", (fw - 150, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    cv2.imshow("BetterDesk Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

if lp:
    if real_mouse:
        pyautogui.mouseUp()
cap.release()
cv2.destroyAllWindows()