import cv2
import numpy as np
import mediapipe as mp
import pyautogui
import math
import time

# ───────────────────────────── Optional: system volume via Pycaw (Windows)
PYCAW_OK = True
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
except Exception:
    PYCAW_OK = False

# ───────────────────────────── MediaPipe setup
mp_hands  = mp.solutions.hands
mp_draw   = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    max_num_hands=1,          # single hand is enough for all modes
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ───────────────────────────── Camera
cap = cv2.VideoCapture(0)
cap.set(3, 960)
cap.set(4, 720)

# ───────────────────────────── Modes
MODES = ["SLIDES", "VOLUME", "CANVAS"]
mode_idx = 0
mode = MODES[mode_idx]

# ───────────────────────────── Slide cooldown state
action_cooldown_frames = 25
cooldown = 0
last_action = ""

# ───────────────────────────── Volume state
if PYCAW_OK:
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        VMIN, VMAX, _ = volume.GetVolumeRange()  # dB range, e.g. (-65.25, 0.0)
    except Exception:
        PYCAW_OK = False

display_vol_pct = 0  # for HUD

# ───────────────────────────── Air Canvas config/state
PALETTE_COLS = [
    ((0, 0, 255), "Red"),
    ((0, 255, 0), "Green"),
    ((255, 0, 0), "Blue"),
    ((0, 255, 255), "Yellow"),
    ((255, 0, 255), "Magenta"),
    ((255, 255, 255), "Eraser"),
    ("CLEAR", "Clear")
]
PALETTE_HEIGHT = 80
PALETTE_BOX_W  = 110
HOVER_SELECT_SECONDS = 0.5
BRUSH_THICKNESS = 8
PALM_CLEAR_SECONDS = 0.6
WINDOW_NAME = "Hand Control (Slides + Volume + Canvas)"

# --- NEW: header area height (matches draw_hud header)
HEADER_HEIGHT = 80

canvas = None                # white background created after first frame
current_color = (0, 0, 255)  # default red (BGR)
current_color_name = "Red"
prev_x, prev_y = None, None
paused = False

hover_start_time = None
hovered_box_idx = None
palm_start_time = None

last_mouse_click = None
def on_mouse(event, x, y, flags, param):
    global last_mouse_click
    if event == cv2.EVENT_LBUTTONDOWN:
        last_mouse_click = (x, y, time.time())

cv2.namedWindow(WINDOW_NAME)
cv2.setMouseCallback(WINDOW_NAME, on_mouse)

# ───────────────────────────── Helpers
def draw_hud(img, mode, last_action, vol_pct):
    h, w = img.shape[:2]
    # Header bar (keep this at the very top)
    cv2.rectangle(img, (0, 0), (w, HEADER_HEIGHT), (30, 30, 30), -1)
    cv2.putText(img, f"Mode: {mode}", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 180), 2)
    if last_action:
        cv2.putText(img, f"Action: {last_action}", (320, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 220, 0), 2)

    # Help footer
    help_text = "1: Slides   2: Volume   3: Canvas    X (Canvas clear)   ESC: Quit"
    cv2.putText(img, help_text, (20, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (220, 220, 220), 2)

    # Volume bar
    if mode == "VOLUME":
        bar_x, bar_y, bar_w, bar_h = 20, 100, 20, 400
        cv2.rectangle(img, (bar_x-2, bar_y-2), (bar_x+bar_w+2, bar_y+bar_h+2), (200, 200, 200), 2)
        fill_h = int((vol_pct / 100.0) * bar_h)
        cv2.rectangle(img, (bar_x, bar_y + bar_h - fill_h), (bar_x + bar_w, bar_y + bar_h), (0, 255, 0), -1)
        cv2.putText(img, f"{vol_pct:3d}%", (bar_x + 30, bar_y + bar_h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

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
            pass

    return pct

def draw_palette(img, frame_w):
    """Draw the palette bar just below the HUD header (so hud doesn't cover it)."""
    y1 = HEADER_HEIGHT
    y2 = y1 + PALETTE_HEIGHT

    for i, (col, name) in enumerate(PALETTE_COLS):
        x1 = i * PALETTE_BOX_W
        x2 = x1 + PALETTE_BOX_W
        if col == "CLEAR":
            cv2.rectangle(img, (x1, y1), (x2, y2), (50, 50, 50), -1)
            cv2.putText(img, "CLEAR", (x1 + 12, y1 + PALETTE_HEIGHT // 2 + 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200, 200, 200), 2, cv2.LINE_AA)
        else:
            cv2.rectangle(img, (x1, y1), (x2, y2), col, -1)
            # label text (use black for colored boxes, black also fine for white/eraser)
            cv2.putText(img, name, (x1 + 8, y2 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (0, 0, 0), 1, cv2.LINE_AA)

        # Highlight hovered box (if any)
        try:
            if hovered_box_idx == i:
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 255), 3)
        except Exception:
            pass

    # current color swatch (place inside palette area on the right)
    sw_x = frame_w - 170
    sw_y = y1 + 12
    cv2.rectangle(img, (sw_x, sw_y), (sw_x + 160, sw_y + 56), (60, 60, 60), -1)
    cv2.putText(img, "Current:", (sw_x + 6, sw_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)
    cv2.rectangle(img, (sw_x + 6, sw_y + 26), (sw_x + 6 + 48, sw_y + 26 + 24),
                  (255, 255, 255) if current_color_name == "Eraser" else current_color, -1)
    cv2.putText(img, current_color_name, (sw_x + 66, sw_y + 44),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)

def get_finger_status(lm):
    """
    Returns list [thumb, index, middle, ring, pinky] where 1 means finger up.
    Thumb measured by comparing x positions (mirrored frame); others by tip.y < pip.y.
    """
    tips = [4, 8, 12, 16, 20]
    status = [0, 0, 0, 0, 0]
    try:
        status[0] = int(lm[tips[0]].x < lm[tips[0] - 1].x)
        for i in range(1, 5):
            status[i] = int(lm[tips[i]].y < lm[tips[i] - 2].y)
    except Exception:
        pass
    return status

def map_fingertip_to_palette(x_px, y_px):
    """Return palette box index under point or None. Accounts for header offset."""
    if HEADER_HEIGHT <= y_px <= (HEADER_HEIGHT + PALETTE_HEIGHT):
        idx = x_px // PALETTE_BOX_W
        if 0 <= idx < len(PALETTE_COLS):
            return int(idx)
    return None

# ───────────────────────────── Main loop
pyautogui.FAILSAFE = False

while True:
    ok, frame = cap.read()
    if not ok:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    h, w = frame.shape[:2]

    # Create canvas once (white background)
    if canvas is None:
        canvas = np.ones_like(frame) * 255

    # Draw landmarks if any hand
    if results.multi_hand_landmarks:
        hand_lms = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(
            frame, hand_lms, mp_hands.HAND_CONNECTIONS,
            mp_styles.get_default_hand_landmarks_style(),
            mp_styles.get_default_hand_connections_style()
        )

        # ───────────── SLIDES
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
            cv2.putText(frame, f"Hand: {label or '?'}", (wx + 10, wy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # ───────────── VOLUME
        elif mode == "VOLUME":
            (x1, y1), (x2, y2), dist = thumb_index_distance(hand_lms.landmark, w, h)
            # Visuals
            cv2.circle(frame, (x1, y1), 10, (255, 0, 0), -1)
            cv2.circle(frame, (x2, y2), 10, (255, 0, 0), -1)
            cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)

            display_vol_pct = set_system_volume_by_distance(dist)
            last_action = f"Volume: {display_vol_pct}%"

        # ───────────── CANVAS
        elif mode == "CANVAS":
            # NOTE: Do NOT draw palette here first (it will be covered by canvas overlay).
            # Palette will be drawn after overlay below so it remains visible on top.

            lm = hand_lms.landmark
            # Index fingertip
            ix = int(lm[8].x * w)
            iy = int(lm[8].y * h)
            fingertip_point = (ix, iy)

            finger_status = get_finger_status(lm)  # [thumb, index, middle, ring, pinky]
            total_up = sum(finger_status)

            # Hover selection on palette (now uses HEADER_HEIGHT-aware mapping)
            hovered_idx = map_fingertip_to_palette(ix, iy)
            if hovered_idx is not None:
                if hovered_box_idx != hovered_idx:
                    hover_start_time = time.time()
                    hovered_box_idx = hovered_idx
                else:
                    if hover_start_time is not None and (time.time() - hover_start_time) >= HOVER_SELECT_SECONDS:
                        box = PALETTE_COLS[hovered_idx][0]
                        name = PALETTE_COLS[hovered_idx][1]
                        if box == "CLEAR":
                            canvas[:] = 255
                            last_action = "Canvas: Cleared (hover)"
                        else:
                            current_color = box
                            current_color_name = name
                            paused = False
                            last_action = f"Canvas Color: {name}"
                        hover_start_time = None
                        hovered_box_idx = None
            else:
                hover_start_time = None
                hovered_box_idx = None

            # Click selection (mouse)
            if last_mouse_click is not None:
                cx, cy, _ = last_mouse_click
                click_idx = map_fingertip_to_palette(cx, cy)
                if click_idx is not None:
                    box = PALETTE_COLS[click_idx][0]
                    name = PALETTE_COLS[click_idx][1]
                    if box == "CLEAR":
                        canvas[:] = 255
                        last_action = "Canvas: Cleared (click)"
                    else:
                        current_color = box
                        current_color_name = name
                        paused = False
                        last_action = f"Canvas Color: {name}"
                last_mouse_click = None

            # Palm clear (all five fingers up and hold)
            if total_up == 5:
                if palm_start_time is None:
                    palm_start_time = time.time()
                else:
                    if (time.time() - palm_start_time) >= PALM_CLEAR_SECONDS:
                        canvas[:] = 255
                        last_action = "Canvas: Cleared (palm hold)"
                        palm_start_time = None
            else:
                palm_start_time = None

            # Draw vs Pause logic
            index_up  = finger_status[1] == 1
            middle_up = finger_status[2] == 1

            # Pause drawing when index + middle are up (and ring/pinky down)
            if index_up and middle_up and not (finger_status[3] or finger_status[4]):
                paused = True
                prev_x, prev_y = None, None
            else:
                only_index_up = index_up and not any([finger_status[0], finger_status[2], finger_status[3], finger_status[4]])
                if only_index_up:
                    paused = False
                    if prev_x is None or prev_y is None:
                        prev_x, prev_y = ix, iy
                    else:
                        draw_col = (255, 255, 255) if current_color_name == "Eraser" else current_color
                        cv2.line(canvas, (prev_x, prev_y), (ix, iy), draw_col, BRUSH_THICKNESS)
                        prev_x, prev_y = ix, iy

            # Show fingertip pointer + status
            cv2.circle(frame, (ix, iy), 8, (0, 120, 255), -1)
            status_text = ("Paused (index+middle)" if paused else f"Drawing ({current_color_name})") if only_index_up or paused else "Idle"
            cv2.putText(frame, f"Canvas: {status_text}", (10, h - 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.72, (240, 240, 240), 2)

    else:
        # No hand: reset some canvas trackers
        if mode == "CANVAS":
            hover_start_time = None
            hovered_box_idx  = None
            palm_start_time  = None
            prev_x, prev_y   = None, None

    # Cooldown tick for slide actions
    if cooldown > 0:
        cooldown -= 1

    # In Canvas mode, overlay canvas onto frame (so drawing persists)
    if mode == "CANVAS":
        gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
        mask_inv = cv2.bitwise_not(mask)
        frame_bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
        canvas_fg = cv2.bitwise_and(canvas, canvas, mask=mask)
        frame = cv2.add(frame_bg, canvas_fg)

        # If palm hold is in-progress, show countdown
        if palm_start_time is not None:
            remaining = max(0.0, PALM_CLEAR_SECONDS - (time.time() - palm_start_time))
            cv2.putText(frame, f"HOLD PALM: {remaining:.1f}s", (w - 260, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 180, 255), 2)

        # ✅ Always draw the palette last so it stays visible (below the header)
        draw_palette(frame, w)

    # HUD (draw after canvas overlay but before showing)
    draw_hud(frame, mode, last_action, display_vol_pct)

    cv2.imshow(WINDOW_NAME, frame)

    # Keys
    key = cv2.waitKey(1) & 0xFF
    if key == 27:              # ESC
        break
    elif key == ord('1'):
        mode = "SLIDES"; last_action = "Switched to SLIDES"
    elif key == ord('2'):
        mode = "VOLUME"; last_action = "Switched to VOLUME"
    elif key == ord('3'):
        mode = "CANVAS"; last_action = "Switched to CANVAS"
    elif key == ord('x') and mode == "CANVAS":
        canvas[:] = 255
        last_action = "Canvas: Cleared (key x)"

cap.release()
cv2.destroyAllWindows()
