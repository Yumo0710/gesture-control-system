import cv2
import mediapipe as mp


class HandDetector:

    def __init__(self, require_mediapipe: bool = True):
        # Try to use MediaPipe solutions; if not available, disable detector gracefully.
        try:
            self.mp_hands = mp.solutions.hands

            self.hands = self.mp_hands.Hands(
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7
            )

            self.mp_draw = mp.solutions.drawing_utils
        except Exception as e:
            print(f"mediapipe 'solutions' not available: {e}. Hand detection disabled.")
            self.mp_hands = None
            self.hands = None
            self.mp_draw = None

    def detect_hands(self, frame):

        # If MediaPipe is not available, return frame without landmarks.
        if self.hands is None:
            return frame, None

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.hands.process(rgb_frame)

        hand_landmarks = None

        if results.multi_hand_landmarks:

            for landmarks in results.multi_hand_landmarks:

                hand_landmarks = landmarks

                # Draw only small keypoint circles (no connecting lines)
                h, w = frame.shape[:2]
                for lm in landmarks.landmark:
                    px = int(lm.x * w)
                    py = int(lm.y * h)
                    cv2.circle(frame, (px, py), 4, (255, 255, 255), -1)

        return frame, hand_landmarks
