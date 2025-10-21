import cv2
import math

class DangerDetector:
    def __init__(self):
        self.last_action = "None"

    def get_distance(self, p1, p2, w, h):
        """Helper to calculate Euclidean distance between 2 landmarks"""
        return math.hypot((p1.x - p2.x) * w, (p1.y - p2.y) * h)

    def detect_gesture(self, lm, w, h):
        """
        Detects gestures based on simple relative distances between fingers.
        Returns a string label for the recognized gesture.
        """
        # Finger tip indices
        tips = [4, 8, 12, 16, 20]
        finger_states = []

        # Thumb
        if lm[tips[0]].x < lm[tips[0] - 1].x:
            finger_states.append(1)
        else:
            finger_states.append(0)

        # Other four fingers
        for i in range(1, 5):
            if lm[tips[i]].y < lm[tips[i] - 2].y:
                finger_states.append(1)
            else:
                finger_states.append(0)

        # ---- Gesture Mapping ----
        if finger_states == [0, 0, 0, 0, 0]:
            return "FIST (DANGER)"
        elif finger_states == [1, 1, 1, 1, 1]:
            return "OPEN PALM (SAFE)"
        elif finger_states == [0, 1, 1, 0, 0]:
            return "V SIGN (VICTORY)"
        elif finger_states == [1, 0, 0, 0, 0]:
            return "THUMBS UP (DISTRESS)"
        else:
            return "UNKNOWN"

    def run(self, frame, results, last_action):
        """Main function to detect gestures"""
        h, w = frame.shape[:2]

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                lm = hand_landmarks.landmark
                gesture = self.detect_gesture(lm, w, h)
                self.last_action = gesture

                # Draw hand landmarks
                for id, lm_point in enumerate(lm):
                    cx, cy = int(lm_point.x * w), int(lm_point.y * h)
                    cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

        # 🟢 Display the detected gesture below the mode label to prevent overlap
        cv2.putText(frame, self.last_action, (50, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 255), 3)

        return frame, self.last_action


# Global instance (so main.py can call danger.run directly)
detector = DangerDetector()

def run(frame, results, last_action):
    return detector.run(frame, results, last_action)
