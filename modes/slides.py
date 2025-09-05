import pyautogui
import math

# Cooldown for slide actions
COOLDOWN_FRAMES = 25
cooldown = 0

def handedness_label(results):
    try:
        return results.multi_handedness[0].classification[0].label  # "Left" or "Right"
    except Exception:
        return None

def run(frame, results, last_action):
    global cooldown

    if results.multi_hand_landmarks:
        hand_lms = results.multi_hand_landmarks[0]
        label = handedness_label(results)

        if label and cooldown == 0:
            if label == "Right":
                pyautogui.press("right")
                last_action = "Next Slide"
                cooldown = COOLDOWN_FRAMES
            elif label == "Left":
                pyautogui.press("left")
                last_action = "Previous Slide"
                cooldown = COOLDOWN_FRAMES

    if cooldown > 0:
        cooldown -= 1

    return frame, last_action
