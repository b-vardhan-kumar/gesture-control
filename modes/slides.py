import pyautogui
import time
import cv2

# cooldown in seconds
COOLDOWN_SECONDS = 0.9
_last_trigger_time = 0.0

# If your camera/mirroring makes slides appear reversed, set this True to flip mapping.
INVERT_HAND_MAPPING = False

def _handedness_label(results):
    try:
        return results.multi_handedness[0].classification[0].label  # "Left" or "Right"
    except Exception:
        return None

def run(frame, results, last_action):
    """
    Use MediaPipe handedness for slide control:
      Right hand  -> Next slide (Right arrow)
      Left hand   -> Previous slide (Left arrow)
    Falls back to index x threshold if handedness not present.
    """
    global _last_trigger_time
    h, w = frame.shape[:2]
    now = time.time()

    if results and results.multi_hand_landmarks:
        hand_lms = results.multi_hand_landmarks[0]

        # draw landmarks for feedback
        mp_draw = cv2
        try:
            # if you want full MediaPipe style drawing uncomment next lines:
            # import mediapipe as mp
            # mp_draw = mp.solutions.drawing_utils
            # mp_draw.draw_landmarks(frame, hand_lms, mp.solutions.hands.HAND_CONNECTIONS)
            pass
        except Exception:
            pass

        label = _handedness_label(results)  # may be "Left" or "Right"

        # use handedness if available
        if label:
            # optionally invert mapping if mirroring is causing reversed behaviour
            if INVERT_HAND_MAPPING:
                if label == "Right":
                    label = "Left"
                elif label == "Left":
                    label = "Right"

            if now - _last_trigger_time > COOLDOWN_SECONDS:
                if label == "Right":
                    pyautogui.press("right")
                    last_action = "Next Slide"
                    _last_trigger_time = now
                elif label == "Left":
                    pyautogui.press("left")
                    last_action = "Previous Slide"
                    _last_trigger_time = now

        else:
            # fallback: use index x position (left third => prev, right third => next)
            try:
                ix = int(hand_lms.landmark[8].x * w)
                if now - _last_trigger_time > COOLDOWN_SECONDS:
                    if ix < w // 3:
                        pyautogui.press("left")
                        last_action = "Previous Slide"
                        _last_trigger_time = now
                    elif ix > 2 * w // 3:
                        pyautogui.press("right")
                        last_action = "Next Slide"
                        _last_trigger_time = now
            except Exception:
                pass

        # Draw a small label near wrist (landmark 0) for feedback
        try:
            wrist = hand_lms.landmark[0]
            wx, wy = int(wrist.x * w), int(wrist.y * h)
            cv2.putText(frame, f"Hand: {label or '?'}", (wx + 10, wy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        except Exception:
            pass

    return frame, last_action
