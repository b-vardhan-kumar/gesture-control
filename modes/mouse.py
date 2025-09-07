import cv2
import pyautogui
import time

# ---------------- Screen size ----------------
SCREEN_W, SCREEN_H = pyautogui.size()

# ---------------- Smoothing ----------------
SMOOTHING = 5
prev_x, prev_y = 0, 0
prev_scroll_x, prev_scroll_y = None, None

# ---------------- Click cooldown ----------------
CLICK_COOLDOWN = 0.5
_last_click_time = 0.0

# ---------------- Scroll sensitivity ----------------
SCROLL_SENSITIVITY = 3  # Increase for faster scroll

def run(frame, results):
    """
    Virtual mouse:
    - Move: index fingertip
    - Left click: pinch thumb+index
    - Right click: pinch thumb+middle
    - Scroll: index+middle extended
        - vertical: hand moves up/down
        - horizontal: hand moves left/right
    """
    global prev_x, prev_y, _last_click_time, prev_scroll_x, prev_scroll_y
    h, w = frame.shape[:2]

    if results.multi_hand_landmarks:
        lm = results.multi_hand_landmarks[0].landmark

        # Finger tips
        index_x, index_y = int(lm[8].x * w), int(lm[8].y * h)
        middle_x, middle_y = int(lm[12].x * w), int(lm[12].y * h)
        thumb_x, thumb_y = int(lm[4].x * w), int(lm[4].y * h)

        # ---------------- Move cursor ----------------
        screen_x = int(index_x / w * SCREEN_W)
        screen_y = int(index_y / h * SCREEN_H)
        smooth_x = prev_x + (screen_x - prev_x) / SMOOTHING
        smooth_y = prev_y + (screen_y - prev_y) / SMOOTHING
        pyautogui.moveTo(smooth_x, smooth_y)
        prev_x, prev_y = smooth_x, smooth_y

        # ---------------- Detect clicks ----------------
        now = time.time()
        distance_index_thumb = ((index_x - thumb_x)**2 + (index_y - thumb_y)**2) ** 0.5
        distance_middle_thumb = ((middle_x - thumb_x)**2 + (middle_y - thumb_y)**2) ** 0.5

        if now - _last_click_time > CLICK_COOLDOWN:
            if distance_index_thumb < 40:
                pyautogui.click()
                _last_click_time = now
            elif distance_middle_thumb < 40:
                pyautogui.click(button='right')
                _last_click_time = now

        # ---------------- Scroll ----------------
        fingers_extended = index_y < middle_y + 20 and middle_y < index_y + 20  # both fingers roughly same y
        if fingers_extended:
            if prev_scroll_x is not None and prev_scroll_y is not None:
                dy = prev_scroll_y - index_y   # vertical scroll
                dx = index_x - prev_scroll_x   # horizontal scroll
                pyautogui.scroll(int(dy * SCROLL_SENSITIVITY))
                pyautogui.hscroll(int(dx * SCROLL_SENSITIVITY))
            prev_scroll_x = index_x
            prev_scroll_y = index_y
        else:
            prev_scroll_x, prev_scroll_y = None, None

        # ---------------- Visual feedback ----------------
        cv2.circle(frame, (index_x, index_y), 10, (0, 0, 255), -1)
        cv2.circle(frame, (middle_x, middle_y), 10, (0, 255, 0), -1)
        cv2.circle(frame, (thumb_x, thumb_y), 10, (255, 0, 0), -1)
        cv2.line(frame, (index_x, index_y), (thumb_x, thumb_y), (0, 255, 255), 2)
        cv2.line(frame, (middle_x, middle_y), (thumb_x, thumb_y), (255, 255, 0), 2)

    return frame
