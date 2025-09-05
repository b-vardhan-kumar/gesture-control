import cv2
import math
import numpy as np

# Optional Pycaw support
PYCAW_OK = True
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)
    VMIN, VMAX, _ = volume.GetVolumeRange()
except Exception:
    PYCAW_OK = False
    volume = None
    VMIN, VMAX = 0, 100

def thumb_index_distance(lms, w, h):
    x1, y1 = int(lms[4].x * w), int(lms[4].y * h)
    x2, y2 = int(lms[8].x * w), int(lms[8].y * h)
    d = math.hypot(x2 - x1, y2 - y1)
    return d

def set_volume(dist, d_min=20, d_max=220):
    dist = np.clip(dist, d_min, d_max)
    pct = int(np.interp(dist, [d_min, d_max], [0, 100]))
    if PYCAW_OK and volume is not None:
        db = np.interp(dist, [d_min, d_max], [VMIN, VMAX])
        try:
            volume.SetMasterVolumeLevel(db, None)
        except:
            pass
    return pct

def run(frame, results, last_action):
    h, w = frame.shape[:2]
    if results.multi_hand_landmarks:
        lms = results.multi_hand_landmarks[0].landmark
        dist = thumb_index_distance(lms, w, h)
        pct = set_volume(dist)
        last_action = f"Volume: {pct}%"

        # Draw visuals
        x1, y1 = int(lms[4].x*w), int(lms[4].y*h)
        x2, y2 = int(lms[8].x*w), int(lms[8].y*h)
        cv2.circle(frame, (x1, y1), 10, (255, 0, 0), -1)
        cv2.circle(frame, (x2, y2), 10, (255, 0, 0), -1)
        cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)
    return frame, last_action
