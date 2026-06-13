import cv2
import mediapipe as mp
import numpy as np


class SimpleLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class SimpleLandmarksContainer:
    def __init__(self, landmarks):
        # landmarks: list of (x,y) normalized
        self.landmark = [SimpleLandmark(x, y) for x, y in landmarks]


class HandDetector:

    def __init__(self, require_mediapipe: bool = True):
        # Try to use MediaPipe solutions; if not available, fall back to OpenCV method.
        try:
            self.mp_hands = mp.solutions.hands

            self.hands = self.mp_hands.Hands(
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7
            )

            self.mp_draw = mp.solutions.drawing_utils
        except Exception as e:
            print(f"mediapipe 'solutions' not available: {e}. Using OpenCV fallback.")
            self.mp_hands = None
            self.hands = None
            self.mp_draw = None

    def _opencv_detect(self, frame):
        # Simple skin color + largest-contour centroid fallback
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # loose skin color range
        lower = np.array([0, 30, 60])
        upper = np.array([25, 200, 255])
        mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.GaussianBlur(mask, (7, 7), 0)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return frame, None

        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        h, w = frame.shape[:2]
        if area < 1200 or area > 0.5 * (h * w):
            return frame, None

        M = cv2.moments(c)
        if M.get('m00', 0) == 0:
            return frame, None
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])

        # optional: draw small red dot for centroid (helps debugging)
        cv2.circle(frame, (cx, cy), 6, (0, 0, 255), -1)

        nx = cx / float(w)
        ny = cy / float(h)

        # return a fake 21-landmark container (palm center duplicated)
        landmarks = [(nx, ny)] * 21
        return frame, SimpleLandmarksContainer(landmarks)

    def detect_hands(self, frame):

        # If MediaPipe is not available, use OpenCV fallback to provide landmarks.
        if self.hands is None:
            return self._opencv_detect(frame)

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
