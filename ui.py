import cv2 as cv
import os

BG=(28,28,30); PANEL=(40,40,45); BLUE=(255,180,40); ORANGE=(0,170,255); WHITE=(240,240,240); GREEN=(60,220,120)

def round_box(img,p1,p2,color,th=2):
    cv.rectangle(img,p1,p2,color,th,cv.LINE_AA)

def draw_top_bar(img,fps=0,status="AI Ready"):
    h,w=img.shape[:2]
    cv.rectangle(img,(0,0),(w,50),PANEL,-1)
    cv.putText(img,"BetterDesk",(20,33),cv.FONT_HERSHEY_SIMPLEX,0.9,WHITE,2,cv.LINE_AA)
    cv.putText(img,status,(220,33),cv.FONT_HERSHEY_SIMPLEX,0.6,GREEN,2,cv.LINE_AA)
    cv.putText(img,f"FPS: {fps:.1f}",(w-120,33),cv.FONT_HERSHEY_SIMPLEX,0.6,WHITE,2,cv.LINE_AA)

def draw_bottom_bar(img,text="Ready"):
    h,w=img.shape[:2]
    cv.rectangle(img,(0,h-40),(w,h),PANEL,-1)
    cv.putText(img,text,(15,h-12),cv.FONT_HERSHEY_SIMPLEX,0.55,WHITE,1,cv.LINE_AA)

def draw_boxes(img,detections,selected=None):
    for x1,y1,x2,y2,lbl,conf in detections:
        c=ORANGE if lbl==selected else BLUE
        round_box(img,(x1,y1),(x2,y2),c,2)
        tw=cv.getTextSize(lbl,cv.FONT_HERSHEY_SIMPLEX,0.5,1)[0][0]
        cv.rectangle(img,(x1,y1-24),(x1+tw+14,y1),c,-1)
        cv.putText(img,lbl,(x1+7,y1-7),cv.FONT_HERSHEY_SIMPLEX,0.5,(20,20,20),1,cv.LINE_AA)

def draw_hand(img,landmarks,connections):
    h,w=img.shape[:2]
    for hl in landmarks:
        for a,b in connections:
            p1=hl[a]; p2=hl[b]
            cv.line(img,(int(p1.x*w),int(p1.y*h)),(int(p2.x*w),int(p2.y*h)),GREEN,2,cv.LINE_AA)
        for i,p in enumerate(hl):
            cv.circle(img,(int(p.x*w),int(p.y*h)),4,WHITE,-1)

def draw_info_panel(img, component, data, organising=False):
    PANEL_W = 320
    h, w = img.shape[:2]
    x = w - PANEL_W

    cv.rectangle(img, (x, 0), (w, h), PANEL, -1)

    cv.putText(img, "Selected", (x + 15, 35),
               cv.FONT_HERSHEY_SIMPLEX, 0.65, WHITE, 2)

    if not component or component not in data:
        cv.putText(img, "Point at a", (x + 20, 90),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 2)
        cv.putText(img, "component...", (x + 20, 120),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 2)
        return

    c = data[component]

    y = 65

    # ---------------- Name ----------------
    cv.putText(img,
               c.get("name", component),
               (x + 15, y),
               cv.FONT_HERSHEY_SIMPLEX,
               0.7,
               BLUE,
               2)

    y += 15

    # ---------------- Image ----------------
    img_path = os.path.join(
        os.path.dirname(__file__),
        c.get("image", "")
    )

    p = None
    if c.get("image"):
        p = cv.imread(img_path)

    if p is not None:
        IMG_W = 220
        IMG_H = 150
        try:
            p = cv.resize(p, (IMG_W, IMG_H))
            ix = x + (PANEL_W - IMG_W) // 2
            img[y:y+IMG_H, ix:ix+IMG_W] = p
            y += IMG_H + 15
        except Exception:
            p = None

    if p is None:
        y += 20
    # ---------------- Description ----------------
    desc = c.get("description", "")
    if desc:
        cv.putText(img,
                   desc[:42],
                   (x + 15, y),
                   cv.FONT_HERSHEY_SIMPLEX,
                   0.42,
                   WHITE,
                   1)

        y += 22

    # ---------------- Specifications ----------------
    cv.putText(img,
               "Specifications",
               (x + 15, y),
               cv.FONT_HERSHEY_SIMPLEX,
               0.52,
               ORANGE,
               2)

    y += 22

    for k, v in c.get("specifications", {}).items():
        if y > h - 120:
            break

        cv.putText(
            img,
            f"{k}: {v}",
            (x + 15, y),
            cv.FONT_HERSHEY_SIMPLEX,
            0.42,
            WHITE,
            1
        )

        y += 18

    # ---------------- Warnings ----------------
    warnings = c.get("warnings", [])

    if warnings and y < h - 90:

        y += 8

        cv.putText(img,
                   "Warnings",
                   (x + 15, y),
                   cv.FONT_HERSHEY_SIMPLEX,
                   0.5,
                   ORANGE,
                   2)

        y += 20

        for wtxt in warnings:

            if y > h - 70:
                break

            cv.putText(
                img,
                "• " + wtxt,
                (x + 20, y),
                cv.FONT_HERSHEY_SIMPLEX,
                0.40,
                WHITE,
                1
            )

            y += 18

    # ---------------- Projects ----------------
    projects = c.get("common_projects", [])

    if projects and y < h - 55:

        y += 5

        cv.putText(img,
                   "Projects",
                   (x + 15, y),
                   cv.FONT_HERSHEY_SIMPLEX,
                   0.5,
                   ORANGE,
                   2)

        y += 20

        for pjt in projects[:3]:

            cv.putText(
                img,
                "• " + pjt,
                (x + 20, y),
                cv.FONT_HERSHEY_SIMPLEX,
                0.40,
                WHITE,
                1
            )

            y += 18

    # ---------------- Organising Banner ----------------
    if organising:
        cv.rectangle(
            img,
            (x + 10, h - 55),
            (w - 10, h - 10),
            ORANGE,
            -1
        )

        cv.putText(
            img,
            "Organising Desk...",
            (x + 20, h - 22),
            cv.FONT_HERSHEY_SIMPLEX,
            0.6,
            WHITE,
            2,
            cv.LINE_AA
        )

def draw(frame,detections,hands,connections,selected,components,fps=0,status="AI Ready",bottom="Ready", organising=False):

    PANEL_W = 320

    h, w = frame.shape[:2]

    # Create a new canvas wider than the camera
    canvas = cv.copyMakeBorder(
        frame,
        0, 0,
        0, PANEL_W,
        cv.BORDER_CONSTANT,
        value=BG
    )

    # Draw the camera UI on the LEFT only
    draw_top_bar(canvas[:, :w], fps, status)
    draw_boxes(canvas[:, :w], detections, selected)
    draw_hand(canvas[:, :w], hands, connections)
    draw_bottom_bar(canvas[:, :w], bottom)

    # Draw the info panel on the RIGHT
    draw_info_panel(canvas, selected, components, organising)

    return canvas


def draw_dashboard(frame, selected, components, fps=0, status="AI Ready", bottom="Ready", organising=False):
    return draw(
        frame,
        [],
        [],
        [],
        selected,
        components,
        fps=fps,
        status=status,
        bottom=bottom,
        organising=organising
    )
