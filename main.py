import cv2
import mediapipe as mp
import numpy as np
import pyautogui

# ------------------------- Modes -------------------------
from modes import slides, volume, canvas

# ------------------------- MediaPipe -------------------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ------------------------- Camera -------------------------
cap = cv2.VideoCapture(0)
cap.set(3, 960)
cap.set(4, 720)

# ------------------------- Mode management -------------------------
MODES = ["SLIDES", "VOLUME", "CANVAS"]
mode = "SLIDES"
last_action = ""

pyautogui.FAILSAFE = False

# ------------------------- Canvas init -------------------------
canvas_frame = None

# ------------------------- Pycaw setup for Volume -------------------------
volume_ctrl = None
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume_ctrl = interface.QueryInterface(IAudioEndpointVolume)
except Exception:
    print("⚠️ Pycaw not available, system volume won't update.")

# ------------------------- Main loop -------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    # ------------------------- Run current mode -------------------------
    if mode == "SLIDES":
        frame, last_action = slides.run(frame, results, last_action)

    elif mode == "VOLUME":
        frame, last_action = volume.run(frame, results, last_action, volume_ctrl)

    elif mode == "CANVAS":
        if canvas_frame is None:
            canvas_frame = 255 * np.ones_like(frame)
        frame, canvas_frame, last_action = canvas.run(frame, canvas_frame, results, last_action)

    # ------------------------- Display -------------------------
    cv2.putText(frame, f"Mode: {mode}", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 180), 2)
    cv2.putText(frame, f"Action: {last_action}", (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 220, 0), 2)

    cv2.imshow("Hand Control", frame)

    # ------------------------- Key Controls -------------------------
    key = cv2.waitKey(1) & 0xFF
    if key == 27:   # ESC
        break
    elif key == ord('1'):
        mode = "SLIDES"; last_action = "Switched to SLIDES"
    elif key == ord('2'):
        mode = "VOLUME"; last_action = "Switched to VOLUME"
    elif key == ord('3'):
        mode = "CANVAS"; last_action = "Switched to CANVAS"
    elif key == ord('x') and mode == "CANVAS":
        if canvas_frame is not None:
            canvas_frame[:] = 255
            last_action = "Canvas cleared"

cap.release()
cv2.destroyAllWindows()
