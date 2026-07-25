"""
BetterDesk Overlay Engine — Demo Script
Run this to verify the overlay system without detector.py.

Usage:
    cd "untitled folder"
    source venv/bin/activate
    python -m overlay.demo

Then open http://<your-mac-ip>:8000 on your iPad.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import time
import overlay as ov

def main():
    ov.start(port=8000)
    print("Waiting 2s for server to be ready…")
    time.sleep(2)

    print("\n[1] Drawing a faint alignment grid…")
    ov.draw_grid(cols=12, rows=8, id_="grid",
                 layer=0, color="rgba(255,255,255,0.08)", thickness=1)
    time.sleep(1)

    print("[2] Highlighting an Arduino bounding box with pulse…")
    h_id = ov.highlight_bbox(
        bbox=(0.10, 0.20, 0.35, 0.55),
        label="Arduino Uno",
        color="#00aaff",
        animation="pulse",
        animationDuration=1200
    )
    time.sleep(1.5)

    print("[3] Glowing circle on the component centre…")
    c_id = ov.draw_circle(
        cx=0.225, cy=0.375, r=0.02,
        color="#00aaff", fillColor="rgba(0,170,255,0.12)",
        animation="glow", animationDuration=800,
        glow="#00aaff", shadow=8, layer=4
    )
    time.sleep(1)

    print("[4] Animated arrow pointing from Arduino to Motor…")
    a_id = ov.draw_arrow(
        start=(0.35, 0.375), end=(0.62, 0.375),
        arrow_type="straight",
        color="#ffaa00",
        animation="move", animationDuration=600,
        thickness=3, glow="#ffaa00", shadow=6, layer=2
    )
    time.sleep(1)

    print("[5] Highlighting Motor with orange pulse…")
    m_id = ov.highlight_bbox(
        bbox=(0.62, 0.22, 0.85, 0.52),
        label="Motor Driver",
        color="#ff6600",
        animation="pulse",
        animationDuration=900
    )
    time.sleep(1)

    print("[6] Placing instructional text…")
    t_id = ov.draw_text(
        0.62, 0.57,
        "Place Motor Here",
        color="#ffffff",
        fillColor="rgba(0,0,0,0.55)",
        fontSize=28,
        animation="fade_in", animationDuration=600,
        layer=3
    )
    time.sleep(0.8)

    print("[7] Bezier wiring path…")
    w_id = ov.draw_bezier(
        0.35, 0.40, 0.45, 0.60, 0.55, 0.20, 0.62, 0.40,
        color="#44ff99", thickness=2.5,
        animation="pulse", animationDuration=1500,
        layer=2
    )
    time.sleep(0.8)

    print("[8] Crosshair on finger position…")
    x_id = ov.draw_crosshair(
        0.225, 0.375, size=0.03,
        color="#ffffff", thickness=1.5,
        animation="blink", animationDuration=600, layer=4
    )
    time.sleep(0.8)

    print("[9] Fading warning text…")
    w2_id = ov.draw_text(
        0.10, 0.62,
        "Wrong Orientation!",
        color="#ff4444",
        fillColor="rgba(60,0,0,0.65)",
        fontSize=24, layer=3,
        animation="blink", animationDuration=500
    )
    time.sleep(2)

    print("\n[Clearing warning in 2s…]")
    time.sleep(2)
    ov.remove(w2_id)
    ov.remove(x_id)

    print("[Updating highlight colour to green…]")
    ov.update(h_id, color="#00ff88", glow="#00ff88")
    time.sleep(2)

    print("[Clearing layer 2 (arrows/paths)…]")
    ov.clear_layer(2)
    time.sleep(2)

    print("[Full clear in 2s…]")
    time.sleep(2)
    ov.clear()

    print("\nDemo complete. Server is still running — open the iPad URL.")
    print("Press Ctrl+C to quit.\n")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
