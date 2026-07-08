import cv2 as cv
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import mediapipe as mp
import sys
import threading
import base64
import requests

c = cv.VideoCapture(0)
if not c.isOpened():
    sys.exit()

o = vision.HandLandmarkerOptions(
    base_options=python.BaseOptions(model_asset_path='hand_landmarker.task'),
    running_mode=vision.RunningMode.IMAGE,
    num_hands=2
)
d = vision.HandLandmarker.create_from_options(o)

cn = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(17,18),(18,19),(19,20),(0,17)]

bd = []
cf = None
act = True

def wk():
    global bd
    s = requests.Session()
    u = 'https://detect.roboflow.com/find-battery-current/11'
    p = {'api_key': '6tPCOrKxxsO95lqJTqkg'}
    while act:
        if cf is not None:
            try:
                cs = cf.copy()
                oh, ow = cs.shape[:2]
                sm = cv.resize(cs, (320, 240))
                _, buf = cv.imencode('.jpg', sm)
                b64 = base64.b64encode(buf).decode('ascii')
                r = s.post(u, params=p, data=b64, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=2).json()
                preds = r.get('predictions', [])
                nb = []
                for pr in preds:
                    if pr['confidence'] > 0.5:
                        x, y, w, h = pr['x'], pr['y'], pr['width'], pr['height']
                        x1 = int((x - w / 2) * ow / 320.0)
                        y1 = int((y - h / 2) * oh / 240.0)
                        x2 = int((x + w / 2) * ow / 320.0)
                        y2 = int((y + h / 2) * oh / 240.0)
                        nb.append((x1, y1, x2, y2, pr['class'], pr['confidence']))
                bd = nb
            except:
                pass
t = threading.Thread(target=wk, daemon=True)
t.start()
while True:
    ok, f = c.read()
    if not ok:
        break
    
    cf = f.copy()
    fh, fw = f.shape[:2]
    
    for x1, y1, x2, y2, lbl, conf in bd:
        cv.rectangle(f, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv.putText(f, "%s %.2f" % (lbl, conf), (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    rgb = cv.cvtColor(f, cv.COLOR_BGR2RGB)
    mi = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    hr = d.detect(mi)
    if hr.hand_landmarks:
        for hl in hr.hand_landmarks:
            for p1, p2 in cn:
                pt1 = hl[p1]
                pt2 = hl[p2]
                cv.line(f, (int(pt1.x * fw), int(pt1.y * fh)), (int(pt2.x * fw), int(pt2.y * fh)), (0, 255, 0), 2)
            for i in [4, 8, 12, 16, 20]:
                pt = hl[i]
                cx, cy = int(pt.x * fw), int(pt.y * fh)
                cv.circle(f, (cx, cy), 8, (0, 0, 255), -1)
                cv.putText(f, str(i), (cx - 10, cy - 15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
    cv.imshow("Combined Tracker", f)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

act = False
c.release()
cv.destroyAllWindows()
d.close()
