import cv2
import time
import pyautogui
import numpy as np

# ---------------- Keyboard Layout ----------------
KEYS = [
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L"],
    ["Z","X","C","V","B","N","M","<"]
]

KEY_ROWS = len(KEYS)
MAX_COLS = max(len(r) for r in KEYS)
KEY_SIZE = (80, 80)  # width, height (increased)
KEY_SPACING = 15      # spacing between keys
TOP_LEFT = (50, 200)  # starting position of the keyboard
HOVER_TIME = 0.5      # seconds to trigger key press

# Hover tracking
hover_start_time = None
hovered_key = None

# Typed text storage
typed_text = ""

# ---------------- Helper Functions ----------------
def draw_keyboard(frame, highlight_key=None):
    """Draw the keyboard layout with optional highlighted key"""
    overlay = frame.copy()
    
    # Draw keys
    for row_idx, row in enumerate(KEYS):
        for col_idx, key in enumerate(row):
            x = TOP_LEFT[0] + col_idx * (KEY_SIZE[0] + KEY_SPACING)
            y = TOP_LEFT[1] + row_idx * (KEY_SIZE[1] + KEY_SPACING)

            # Transparent key base
            base_color = (200, 200, 200)
            alpha = 0.5  # transparency
            cv2.rectangle(overlay, (x, y), (x + KEY_SIZE[0], y + KEY_SIZE[1]), base_color, -1)

            # Highlight key
            if highlight_key == key:
                cv2.rectangle(overlay, (x, y), (x + KEY_SIZE[0], y + KEY_SIZE[1]), (0, 200, 0), -1)

            # Key borders
            cv2.rectangle(overlay, (x, y), (x + KEY_SIZE[0], y + KEY_SIZE[1]), (0, 0, 0), 2)
            
            # Key text
            cv2.putText(overlay, key, (x + 20, y + 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)

    # Overlay the transparent keys onto the frame
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    # Draw typed text box
    text_box_width = MAX_COLS * (KEY_SIZE[0] + KEY_SPACING) - KEY_SPACING
    cv2.rectangle(frame, (TOP_LEFT[0], TOP_LEFT[1] - 100),
                  (TOP_LEFT[0] + text_box_width, TOP_LEFT[1] - 20), (255, 255, 255), -1)
    cv2.rectangle(frame, (TOP_LEFT[0], TOP_LEFT[1] - 100),
                  (TOP_LEFT[0] + text_box_width, TOP_LEFT[1] - 20), (0, 0, 0), 2)
    cv2.putText(frame, typed_text, (TOP_LEFT[0] + 10, TOP_LEFT[1] - 45),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)

    return frame

def get_hovered_key(ix, iy):
    """Return the key that the fingertip is currently hovering over"""
    for row_idx, row in enumerate(KEYS):
        for col_idx, key in enumerate(row):
            x = TOP_LEFT[0] + col_idx * (KEY_SIZE[0] + KEY_SPACING)
            y = TOP_LEFT[1] + row_idx * (KEY_SIZE[1] + KEY_SPACING)
            if x <= ix <= x + KEY_SIZE[0] and y <= iy <= y + KEY_SIZE[1]:
                return key
    return None

# ---------------- Main Run Function ----------------
def run(frame, results, last_action):
    global hover_start_time, hovered_key, typed_text

    h, w = frame.shape[:2]
    highlight_key = None

    if results.multi_hand_landmarks:
        lms = results.multi_hand_landmarks[0].landmark
        ix, iy = int(lms[8].x * w), int(lms[8].y * h)  # index fingertip

        key = get_hovered_key(ix, iy)
        if key:
            highlight_key = key
            if hovered_key != key:
                hover_start_time = time.time()
                hovered_key = key
            else:
                if hover_start_time and (time.time() - hover_start_time) >= HOVER_TIME:
                    # Press the key
                    if key == "<":
                        typed_text = typed_text[:-1]
                        pyautogui.press("backspace")
                        last_action = "Backspace"
                    else:
                        typed_text += key
                        pyautogui.press(key.lower())
                        last_action = f"Key: {key}"
                    hover_start_time = None
                    hovered_key = None
        else:
            hover_start_time = None
            hovered_key = None

        # Draw fingertip pointer
        cv2.circle(frame, (ix, iy), 15, (0, 0, 255), -1)

    # Draw the keyboard and typed text
    frame = draw_keyboard(frame, highlight_key)
    return frame, last_action
