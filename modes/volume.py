import cv2
import numpy as np
import math

# Volume control module
# Uses thumb + index finger pinch distance to control system volume
# You can integrate with pycaw for Windows volume or just show value for now

def run(frame, results, last_action, volume_ctrl=None):
    """
    Adjust system volume using hand pinch gesture.
    Thumb tip (4) and Index tip (8) distance -> volume level.
    """
    h, w = frame.shape[:2]

    if results and results.multi_hand_landmarks:
        hand_lms = results.multi_hand_landmarks[0]  # get first hand
        lm = hand_lms.landmark

        # Thumb tip (4), Index tip (8)
        x1, y1 = int(lm[4].x * w), int(lm[4].y * h)
        x2, y2 = int(lm[8].x * w), int(lm[8].y * h)

        # Draw circles on tips
        cv2.circle(frame, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
        cv2.circle(frame, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
        cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)

        # Distance between points
        length = math.hypot(x2 - x1, y2 - y1)

        # Map length to volume [0, 100]
        vol = np.interp(length, [20, 200], [0, 100])

        if volume_ctrl:  # if pycaw or similar object is passed
            volume_ctrl.SetMasterVolumeLevelScalar(vol / 100, None)

        last_action = f"Volume: {int(vol)}%"

        # Draw volume bar
        cv2.rectangle(frame, (50, 150), (85, 400), (0, 255, 0), 2)
        bar = np.interp(vol, [0, 100], [400, 150])
        cv2.rectangle(frame, (50, int(bar)), (85, 400), (0, 255, 0), cv2.FILLED)
        cv2.putText(frame, f'{int(vol)} %', (40, 430),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    return frame, last_action
