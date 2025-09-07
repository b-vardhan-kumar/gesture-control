import cv2
import pyautogui
import time

# Keyboard layout (rows of keys)
KEY_LAYOUT = [
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
    ["SPACE", "ENTER", "BACK"]
]

KEY_W, KEY_H = 80, 80
HOVER_TIME = 0.7  # seconds to "press" key

hover_start = None
hovered_key = None

def draw_keyboard(frame, h, w):
    """Draw keyboard on screen and return key bounding boxes."""
    key_boxes = []
    start_y = h - (len(KEY_LAYOUT) * KEY_H) - 20

    for row_idx, row in enumerate(KEY_LAYOUT):
        start_x = (w - len(row) * KEY_W) // 2
        for col_idx, key in enumerate(row):
            x1 = start_x + col_idx * KEY_W
            y1 = start_y + row_idx * KEY_H
            x2, y2 = x1 + KEY_W, y1 + KEY_H
            key_boxes.append((x1, y1, x2, y2, key))
            cv2.rectangle(frame, (x1, y1), (x2, y2), (200, 200, 200), 2)
            label = "␣" if key == "SPACE" else key
            cv2.putText(frame, label, (x1+10, y1+50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    return key_boxes

def run(frame, hand_lms):
    global hover_start, hovered_key
    h, w = frame.shape[:2]

    # Draw keyboard
    key_boxes = draw_keyboard(frame, h, w)

    if not hand_lms:
        hover_start, hovered_key = None, None
        return frame

    # Get fingertip position
    lm = hand_lms.landmark
    ix, iy = int(lm[8].x * w), int(lm[8].y * h)
    cv2.circle(frame, (ix, iy), 12, (0, 255, 0), -1)

    # Check if fingertip is inside any key
    for (x1, y1, x2, y2, key) in key_boxes:
        if x1 <= ix <= x2 and y1 <= iy <= y2:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
            if hovered_key != key:
                hovered_key = key
                hover_start = time.time()
            else:
                if time.time() - hover_start > HOVER_TIME:
                    # Trigger keypress
                    if key == "SPACE":
                        pyautogui.press("space")
                    elif key == "ENTER":
                        pyautogui.press("enter")
                    elif key == "BACK":
                        pyautogui.press("backspace")
                    else:
                        pyautogui.press(key.lower())
                    hover_start = time.time()  # reset for repeat press
                    cv2.putText(frame, f"Pressed: {key}", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 3)
            break
    else:
        hovered_key, hover_start = None, None

    return frame
