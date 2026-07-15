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

def draw_info_panel(img,component,data):
    PANEL_W = 320
    h, w = img.shape[:2]
    x = w - PANEL_W
    cv.rectangle(img,(x, 0),(w, h),PANEL,-1)
    cv.putText(img,"Selected",(x+15,80),cv.FONT_HERSHEY_SIMPLEX,0.6,WHITE,2)
    if not component or component not in data:
        cv.putText(img,"Point at a",(x+20,140),cv.FONT_HERSHEY_SIMPLEX,0.7,WHITE,2)
        cv.putText(img,"component...",(x+20,170),cv.FONT_HERSHEY_SIMPLEX,0.7,WHITE,2)
        return
    c=data[component]
    y=120
    cv.putText(img,c.get("name",component),(x+15,y),cv.FONT_HERSHEY_SIMPLEX,0.7,BLUE,2); y+=30
    cv.putText(img,c.get("description",""),(x+15,y),cv.FONT_HERSHEY_SIMPLEX,0.45,WHITE,1); y+=35
    for k,v in c.get("specifications",{}).items():
        if not v: continue
        cv.putText(img,f"{k}: {v}",(x+15,y),cv.FONT_HERSHEY_SIMPLEX,0.48,WHITE,1)
        y+=22
    pin=c.get("pinout","")
    if pin and os.path.exists(pin):
        p=cv.imread(pin)
        if p is not None:
            p=cv.resize(p,(280,200))
            img[y:y+200,x+15:x+295]=p

def draw(frame, detections, hands, connections, selected, components,
         fps=0, status="AI Ready", bottom="Ready"):

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
    draw_info_panel(canvas, selected, components)

    return canvas
