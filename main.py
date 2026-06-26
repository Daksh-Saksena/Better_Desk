import cv2
import mediapipe as mp

c0 = cv2.VideoCapture(0)
c1 = cv2.VideoCapture(1)
mp_h = mp.solutions.hands
mp_d = mp.solutions.drawing_utils
hands = mp_h.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)
while True:
    ok0, im0 = c0.read()
    ok1, im1 = c1.read()
    if not ok0 or not ok1:
        break
    im0 = cv2.resize(cv2.flip(im0, 1), (640, 480))
    im1 = cv2.resize(cv2.flip(im1, 1), (640, 480))
    rgb0 = cv2.cvtColor(im0, cv2.COLOR_BGR2RGB)
    rgb1 = cv2.cvtColor(im1, cv2.COLOR_BGR2RGB)
    res0 = hands.process(rgb0)

    if res0.multi_hand_landmarks:
        h = res0.multi_hand_landmarks[0]
        mp_d.draw_landmarks(im0, h, mp_h.HAND_CONNECTIONS)
        tip = h.landmark[8]
        x = int(tip.x * im0.shape[1])
        y = int(tip.y * im0.shape[0])
        cv2.circle(im0, (x, y), 15, (0, 255, 0), -1)
        cv2.putText(im0, f"{x},{y}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    res1 = hands.process(rgb1)
    if res1.multi_hand_landmarks:
        h = res1.multi_hand_landmarks[0]
        mp_d.draw_landmarks(im1, h, mp_h.HAND_CONNECTIONS)
        tip = h.landmark[8]
        x = int(tip.x * im1.shape[1])
        y = int(tip.y * im1.shape[0])
        cv2.circle(im1, (x, y), 15, (0, 255, 0), -1)
        cv2.putText(im1, f"{x},{y}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(im0, "TOP VIEW", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(im1, "SIDE VIEW", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    combo = cv2.hconcat([im0, im1])
    cv2.imshow("BetterDesk Vision System", combo)
    if cv2.waitKey(1) == ord("q"):
        break

c0.release()
c1.release()
cv2.destroyAllWindows()