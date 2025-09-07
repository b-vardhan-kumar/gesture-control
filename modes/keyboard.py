import cv2
import time
import pyautogui

# ---------------- Keyboard Layout ----------------
KEYS = [
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L"],
    ["Z","X","C","V","B","N","M","<"],
    ["SPACE"]
]

KEY_ROWS = len(KEYS)
MAX_COLS = max(len(r) for r in KEYS)
KEY_SIZE = (80, 80)  # increased for bigger window
KEY_SPACING = 15
TOP_LEFT = (50, 300)  # adjusted for bigger window
HOVER_TIME = 0.5  # seconds for key press

hover_start_time = None
hovered_key = None
typed_text = ""

# ---------------- Helper Functions ----------------
def draw_keyboard(frame, highlight_key=None):
    """Draw the keyboard layout and highlight hovered/pressed key"""
    for row_idx, row in enumerate(KEYS):
        for col_idx, key in enumerate(row):
            if key == "SPACE":
                x = TOP_LEFT[0]
                y = TOP_LEFT[1] + row_idx*(KEY_SIZE[1]+KEY_SPACING)
                w_key = KEY_SIZE[0]*5
                h_key = KEY_SIZE[1]
            else:
                x = TOP_LEFT[0] + col_idx*(KEY_SIZE[0]+KEY_SPACING)
                y = TOP_LEFT[1] + row_idx*(KEY_SIZE[1]+KEY_SPACING)
                w_key, h_key = KEY_SIZE

            color = (200,200,200)
            if highlight_key == key:
                color = (0,200,0)  # highlight in green

            cv2.rectangle(frame, (x,y), (x+w_key, y+h_key), color, -1)
            cv2.rectangle(frame, (x,y), (x+w_key, y+h_key), (0,0,0), 2)
            cv2.putText(frame, key if key!="SPACE" else "SPACE", (x+15, y+50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)

    # Draw typed text box
    cv2.rectangle(frame, (TOP_LEFT[0], TOP_LEFT[1]-100),
                  (TOP_LEFT[0]+MAX_COLS*(KEY_SIZE[0]+KEY_SPACING)-KEY_SPACING, TOP_LEFT[1]-20),
                  (255,255,255), -1)
    cv2.rectangle(frame, (TOP_LEFT[0], TOP_LEFT[1]-100),
                  (TOP_LEFT[0]+MAX_COLS*(KEY_SIZE[0]+KEY_SPACING)-KEY_SPACING, TOP_LEFT[1]-20),
                  (0,0,0), 2)
    cv2.putText(frame, typed_text, (TOP_LEFT[0]+10, TOP_LEFT[1]-40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
    return frame

def get_hovered_key(ix, iy):
    """Return key that the fingertip is hovering over"""
    for row_idx, row in enumerate(KEYS):
        for col_idx, key in enumerate(row):
            if key == "SPACE":
                x = TOP_LEFT[0]
                y = TOP_LEFT[1] + row_idx*(KEY_SIZE[1]+KEY_SPACING)
                w_key = KEY_SIZE[0]*5
                h_key = KEY_SIZE[1]
            else:
                x = TOP_LEFT[0] + col_idx*(KEY_SIZE[0]+KEY_SPACING)
                y = TOP_LEFT[1] + row_idx*(KEY_SIZE[1]+KEY_SPACING)
                w_key, h_key = KEY_SIZE

            if x <= ix <= x+w_key and y <= iy <= y+h_key:
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
                if hover_start_time and (time.time()-hover_start_time) >= HOVER_TIME:
                    if key == "<":
                        typed_text = typed_text[:-1]
                        pyautogui.press("backspace")
                        last_action = "Backspace"
                    elif key == "SPACE":
                        typed_text += " "
                        pyautogui.press("space")
                        last_action = "Space"
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
        cv2.circle(frame, (ix, iy), 10, (0,0,255), -1)

    # Draw keyboard and typed text
    frame = draw_keyboard(frame, highlight_key)
    return frame, last_action
