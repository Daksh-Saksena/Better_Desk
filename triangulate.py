import cv2
import mediapipe as mp
import numpy as np
import pygame
import sys

corners = []
lx = None
ly = None
st = np.load("stereo.npz")
p0_mat = st["P0"]
p1_mat = st["P1"]
c0 = cv2.VideoCapture(0)
c1 = cv2.VideoCapture(1)
mp_h = mp.solutions.hands
mp_d = mp.solutions.drawing_utils
h0 = mp_h.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.6)
h1 = mp_h.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.6)

pygame.init()
w, h = 1000, 700
scr = pygame.display.set_mode((w, h))

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    ok0, im0 = c0.read()
    ok1, im1 = c1.read()
    if not ok0 or not ok1:
        break
    rgb0 = cv2.cvtColor(im0, cv2.COLOR_BGR2RGB)
    rgb1 = cv2.cvtColor(im1, cv2.COLOR_BGR2RGB)
    res0 = h0.process(rgb0)
    res1 = h1.process(rgb1)
    p0 = None
    p1 = None

    if res0.multi_hand_landmarks:
        hand0 = res0.multi_hand_landmarks[0]
        mp_d.draw_landmarks(im0, hand0, mp_h.HAND_CONNECTIONS)
        tip0 = hand0.landmark[8]
        x0 = int(tip0.x * im0.shape[1])
        y0 = int(tip0.y * im0.shape[0])
        p0 = (x0, y0)
        cv2.circle(im0, (x0, y0), 15, (0, 255, 0), -1)

    if res1.multi_hand_landmarks:
        hand1 = res1.multi_hand_landmarks[0]
        mp_d.draw_landmarks(im1, hand1, mp_h.HAND_CONNECTIONS)
        tip1 = hand1.landmark[8]
        x1 = int(tip1.x * im1.shape[1])
        y1 = int(tip1.y * im1.shape[0])
        p1 = (x1, y1)
        cv2.circle(im1, (x1, y1), 15, (0, 255, 0), -1)

    if p0 is not None and p1 is not None:
        pts4d = cv2.triangulatePoints(
            p0_mat,
            p1_mat,
            np.array([[p0[0]], [p0[1]]], dtype=np.float32),
            np.array([[p1[0]], [p1[1]]], dtype=np.float32)
        )
        pts4d /= pts4d[3]
        x_coord = pts4d[0, 0]
        y_coord = pts4d[1, 0]
        z_coord = pts4d[2, 0]
        lx = x_coord
        ly = y_coord
        scr.fill((255, 255, 255))
        pygame.draw.circle(scr, (0, 100, 255), (w // 2, h // 2), 20)
        pygame.display.set_caption(f"X={x_coord:.1f} Y={y_coord:.1f} Z={z_coord:.1f}")
        pygame.display.flip()
        cv2.putText(im0, f"X:{x_coord:.1f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(im0, f"Y:{y_coord:.1f}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(im0, f"Z:{z_coord:.1f}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    d0 = cv2.resize(im0, (640, 360))
    d1 = cv2.resize(im1, (640, 360))
    combo = cv2.hconcat([d0, d1])
    cv2.imshow("BetterDesk 3D Tracker", combo)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("m") and lx is not None:
        corners.append((lx, ly))
        print(f"CORNER {len(corners)}: {lx:.1f}, {ly:.1f}")
        if len(corners) == 4:
            print("DONE:")
            print(corners)
    if key == ord("q"):
        break
c0.release()
c1.release()
cv2.destroyAllWindows()
pygame.quit()