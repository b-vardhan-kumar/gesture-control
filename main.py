import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import math
import time

# ── Optional: system volume via Pycaw (Windows)
PYCAW_OK = True
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
except Exception:
    PYCAW_OK = False

# ── MediaPipe setup
mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ── Camera
cap = cv2.VideoCapture(0)
cap.set(3, 960)
cap.set(4, 720)

# ── Modes
MODES = ["SLIDES", "VOLUME"]
mode_idx = 0
mode = MODES[mode_idx]

# ── Slide cooldown state
action_cooldown_frames = 25
cooldown = 0
last_action = ""

# ── Volume state
if PYCAW_OK:
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        VMIN, VMAX, _ = volume.GetVolumeRange()  # dB range, e.g. (-65.25, 0.0)
    except Exception:
        PYCAW_OK = False

# For the HUD volume bar (also used if Pycaw unavailable)
display_vol_pct = 0

# ── Helpers
def draw_hud(img, mode, last_action, vol_pct):
    h, w = img.shape[:2]
    # Header bar
    cv2.rectangle(img, (0,0), (w, 80), (30,30,30), -1)
    cv2.putText(img, f"Mode: {mode}", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,255,180), 2)
    if last_action:
        cv2.putText(img, f"Action: {last_action}", (320, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255,220,0), 2)

    # Help
    help_text = "S: Slides  V: Volume  M: Cycle  ESC: Quit"
    cv2.putText(img, help_text, (20, h-20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (220,220,220), 2)

    # Volume bar (always visible in VOLUME mode; hidden in SLIDES mode unless you want it)
    if mode == "VOLUME":
        bar_x, bar_y, bar_w, bar_h = 20, 100, 20, 400
        cv2.rectangle(img, (bar_x-2, bar_y-2), (bar_x+bar_w+2, bar_y+bar_h+2), (200,200,200), 2)
        fill_h = int((vol_pct/100.0) * bar_h)
        cv2.rectangle(img, (bar_x, bar_y+bar_h-fill_h), (bar_x+bar_w, bar_y+bar_h), (0,255,0), -1)
        cv2.putText(img, f"{vol_pct:3d}%", (bar_x+30, bar_y+bar_h-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

def thumb_index_distance(lms, w, h):
    # Landmarks: 4 = thumb tip, 8 = index tip
    x1, y1 = int(lms[4].x * w),  int(lms[4].y * h)
    x2, y2 = int(lms[8].x * w),  int(lms[8].y * h)
    d = math.hypot(x2 - x1, y2 - y1)
    return (x1, y1), (x2, y2), d

def handedness_label(results):
    try:
        return results.multi_handedness[0].classification[0].label  # "Left" or "Right"
    except Exception:
        return None

def set_system_volume_by_distance(dist, d_min=20, d_max=220):
    """
    Map thumb-index distance [d_min, d_max] to system volume 0..100% (and to dB if Pycaw available).
    Returns pct for HUD.
    """
    dist = np.clip(dist, d_min, d_max)
    pct = int(np.interp(dist, [d_min, d_max], [0, 100]))

    if PYCAW_OK:
        # Map to dB
        db = np.interp(dist, [d_min, d_max], [VMIN, VMAX])
        try:
            volume.SetMasterVolumeLevel(db, None)
        except Exception:
            pass  # if something goes wrong, at least keep HUD working

    return pct

# ── Main loop
while True:
    ok, frame = cap.read()
    if not ok:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    h, w = frame.shape[:2]

    if results.multi_hand_landmarks:
        hand_lms = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(
            frame, hand_lms, mp_hands.HAND_CONNECTIONS,
            mp_styles.get_default_hand_landmarks_style(),
            mp_styles.get_default_hand_connections_style()
        )

        # Current mode behaviors
        if mode == "SLIDES":
            label = handedness_label(results)  # "Left" or "Right"
            if label and cooldown == 0:
                if label == "Right":
                    pyautogui.press("right")
                    last_action = "Next Slide"
                    cooldown = action_cooldown_frames
                elif label == "Left":
                    pyautogui.press("left")
                    last_action = "Previous Slide"
                    cooldown = action_cooldown_frames

            # Draw label near wrist
            wrist = hand_lms.landmark[0]
            wx, wy = int(wrist.x * w), int(wrist.y * h)
            cv2.putText(frame, f"Hand: {label or '?'}", (wx+10, wy-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        elif mode == "VOLUME":
            (x1, y1), (x2, y2), dist = thumb_index_distance(hand_lms.landmark, w, h)
            # Visuals
            cv2.circle(frame, (x1, y1), 10, (255, 0, 0), -1)
            cv2.circle(frame, (x2, y2), 10, (255, 0, 0), -1)
            cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cx, cy = (x1+x2)//2, (y1+y2)//2
            cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)

            display_vol_pct = set_system_volume_by_distance(dist)
            last_action = f"Volume: {display_vol_pct}%"

    # Cooldown tick
    if cooldown > 0:
        cooldown -= 1

    # HUD
    draw_hud(frame, mode, last_action, display_vol_pct)

    cv2.imshow("Hand Control (Slides + Volume)", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == 27:           # ESC
        break
    elif key in (ord('m'), ord('M')):
        mode_idx = (mode_idx + 1) % len(MODES)
        mode = MODES[mode_idx]
        last_action = f"Switched to {mode}"
    elif key in (ord('s'), ord('S')):
        mode = "SLIDES"; last_action = "Switched to SLIDES"
    elif key in (ord('v'), ord('V')):
        mode = "VOLUME"; last_action = "Switched to VOLUME"

cap.release()
cv2.destroyAllWindows()
