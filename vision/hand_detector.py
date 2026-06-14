import cv2
import math
import os
import urllib.request


class SimpleLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class SimpleLandmarksContainer:
    def __init__(self, landmarks):
        # landmarks: list of (x,y) normalized
        self.landmark = [SimpleLandmark(x, y) for x, y in landmarks]


class HandDetector:
    """Robust hand detector:

    Strategy:
    1. Try MediaPipe Tasks API (HandLandmarker) with model download support.
    2. Fallback: improved OpenCV contour-based palm detector.
    """

    def __init__(self, require_mediapipe: bool = True):

        self.mode = None
        self.hand_detector = None

        # Try MediaPipe Tasks API (HandLandmarker)
        try:
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            # Ensure model directory and file
            model_dir = os.path.join(os.getcwd(), "vision_models")
            os.makedirs(model_dir, exist_ok=True)
            model_path = os.path.join(model_dir, "hand_landmarker.task")

            # Download model if not exists (try multiple URLs)
            if not os.path.exists(model_path):
                print(f"Downloading hand_landmarker.task to {model_path}...")
                urls = [
                    "https://storage.googleapis.com/mediapipe-models/hand_landmarker.task",
                    "https://storage.googleapis.com/mediapipe-assets/hand_landmarker.task",
                ]
                downloaded = False
                for url in urls:
                    try:
                        urllib.request.urlretrieve(url, model_path)
                        print(f"Download complete from {url}")
                        downloaded = True
                        break
                    except Exception as e:
                        print(f"Download from {url} failed: {e}")
                        continue
                
                if not downloaded:
                    print("All download URLs failed, will use OpenCV fallback.")
                    model_path = None

            if model_path and os.path.exists(model_path):
                # Create HandLandmarker without running_mode parameter
                base_options = python.BaseOptions(model_asset_path=model_path)
                options = vision.HandLandmarkerOptions(
                    base_options=base_options,
                    num_hands=1,
                    min_hand_detection_confidence=0.7,
                    min_hand_presence_confidence=0.7,
                    min_tracking_confidence=0.7,
                )
                self.hand_detector = vision.HandLandmarker.create_from_options(options)
                self.mode = "tasks"
                print("HandLandmarker mode: OK")

        except Exception as e:
            print(f"HandLandmarker setup failed: {e}, falling back to OpenCV.")
            self.mode = None
            self.hand_detector = None

        # Final fallback: OpenCV contour method
        if self.mode is None:
            self.mode = "opencv"
            print("Using OpenCV detector mode.")

    def _mediapipe_detect(self, frame):
        """Use MediaPipe Tasks API (HandLandmarker) to detect hands."""
        try:
            from mediapipe.tasks.python.vision.core import image as mp_image

            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Create MediaPipe Image from numpy array
            mp_img = mp_image.Image(image_format=mp_image.ImageFormat.SRGB, data=rgb_frame)

            # Run detection
            result = self.hand_detector.detect(mp_img)

            if result.hand_landmarks and len(result.hand_landmarks) > 0:
                # Get first hand - result.hand_landmarks[0] is a list of NormalizedLandmark objects
                hand_landmarks_list = result.hand_landmarks[0]

                # Convert to compatible format: list of (x, y) tuples
                landmarks = []
                h, w = frame.shape[:2]

                for lm in hand_landmarks_list:
                    x = lm.x
                    y = lm.y
                    landmarks.append((x, y))

                    # Draw landmark on frame
                    px = int(x * w)
                    py = int(y * h)
                    cv2.circle(frame, (px, py), 3, (0, 255, 0), -1)

                # Draw lines between key landmarks (simple hand skeleton)
                connections = [
                    (0, 1), (1, 2), (2, 3), (3, 4),  # thumb
                    (0, 5), (5, 6), (6, 7), (7, 8),  # index
                    (0, 9), (9, 10), (10, 11), (11, 12),  # middle
                    (0, 13), (13, 14), (14, 15), (15, 16),  # ring
                    (0, 17), (17, 18), (18, 19), (19, 20),  # pinky
                ]
                for start, end in connections:
                    if start < len(landmarks) and end < len(landmarks):
                        x1, y1 = landmarks[start]
                        x2, y2 = landmarks[end]
                        cv2.line(frame, (int(x1 * w), int(y1 * h)), (int(x2 * w), int(y2 * h)), (0, 255, 0), 1)

                return frame, SimpleLandmarksContainer(landmarks)
            else:
                return frame, None

        except Exception as e:
            print(f"MediaPipe detection error: {e}")
            return frame, None

    def _get_fingertips(self, contour, palm_center, w, h):
        hull = cv2.convexHull(contour, returnPoints=True)
        if hull is None or len(hull) == 0:
            return []

        hull_pts = [tuple(pt[0]) for pt in hull]
        candidates = []
        palm_x, palm_y = palm_center

        for i in range(len(hull_pts)):
            prev_pt = hull_pts[i - 1]
            curr_pt = hull_pts[i]
            next_pt = hull_pts[(i + 1) % len(hull_pts)]

            # Must be above the palm center and reasonably far away
            if curr_pt[1] > palm_y + 20:
                continue

            def vec(a, b):
                return (b[0] - a[0], b[1] - a[1])

            v1 = vec(curr_pt, prev_pt)
            v2 = vec(curr_pt, next_pt)
            dot = v1[0] * v2[0] + v1[1] * v2[1]
            mag1 = math.hypot(v1[0], v1[1])
            mag2 = math.hypot(v2[0], v2[1])
            if mag1 == 0 or mag2 == 0:
                continue

            angle = math.acos(max(-1.0, min(1.0, dot / (mag1 * mag2))))
            distance = math.hypot(curr_pt[0] - palm_x, curr_pt[1] - palm_y)

            # fingertip candidate should have a sharp hull angle and be outside the palm
            if angle < 1.3 and distance > 0.08 * max(w, h):
                candidates.append((curr_pt[0], curr_pt[1], distance))

        # Remove duplicates by spatial proximity
        filtered = []
        for x, y, dist in sorted(candidates, key=lambda item: item[2], reverse=True):
            if not any(math.hypot(x - fx, y - fy) < 25 for fx, fy, _ in filtered):
                filtered.append((x, y, dist))

        return [(x, y) for x, y, _ in filtered[:5]]

    def _approximate_landmarks(self, tips, palm_center, w, h):
        palm_x, palm_y = palm_center

        if len(tips) < 5:
            # If fingertips are missing, approximate from contour extremes
            tips = sorted(tips, key=lambda p: (p[1], p[0]))
            while len(tips) < 5:
                tips.append((palm_x, palm_y))

        # Thumb is the tip furthest horizontally from palm center
        thumb_tip = max(tips, key=lambda p: abs(p[0] - palm_x))
        remaining = [p for p in tips if p != thumb_tip]
        remaining = sorted(remaining, key=lambda p: p[0])

        # If we have fewer than 4 other fingers, pad with palm edge points
        while len(remaining) < 4:
            remaining.append((palm_x, palm_y - int(0.15 * h)))

        ordered_tips = [thumb_tip] + remaining[:4]

        landmarks = [SimpleLandmark(palm_x / w, palm_y / h)]

        def interpolate(point_a, point_b, ratio):
            return (
                point_a[0] + (point_b[0] - point_a[0]) * ratio,
                point_a[1] + (point_b[1] - point_a[1]) * ratio,
            )

        for tip in ordered_tips:
            for ratio in (0.25, 0.5, 0.75, 1.0):
                x, y = interpolate((palm_x, palm_y), tip, ratio)
                landmarks.append(SimpleLandmark(x / w, y / h))

        # Ensure exactly 21 landmarks
        if len(landmarks) > 21:
            landmarks = landmarks[:21]
        while len(landmarks) < 21:
            landmarks.append(SimpleLandmark(palm_x / w, palm_y / h))

        return landmarks

    def _opencv_detect(self, frame):
        """OpenCV-based hand detection using skin color and shape analysis."""
        h, w = frame.shape[:2]
        frame_area = h * w

        # Skin detection: combine HSV and YCrCb thresholds
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_hsv = (0, 30, 60)
        upper_hsv = (20, 150, 255)
        mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)

        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        lower_ycrcb = (0, 133, 77)
        upper_ycrcb = (255, 173, 127)
        mask_ycrcb = cv2.inRange(ycrcb, lower_ycrcb, upper_ycrcb)

        mask = cv2.bitwise_and(mask_hsv, mask_ycrcb)

        # Morphological operations
        mask = cv2.GaussianBlur(mask, (7, 7), 0)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None

        # Get largest contour
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)

        # Area checks: reject very small or very large (likely full body)
        if area < 1500 or area > 0.20 * frame_area:
            return None, None

        # Bounding box checks
        x, y, bw, bh = cv2.boundingRect(c)
        bbox_area = bw * bh
        extent = float(area) / bbox_area if bbox_area > 0 else 0

        # Expect solid blob
        if extent < 0.25 or extent > 0.95:
            return None, None

        # Bbox relative size: palm shouldn't be majority of frame
        if bh > 0.8 * h or bw > 0.8 * w:
            return None, None

        # Aspect ratio check
        aspect = float(bw) / bh if bh > 0 else 0
        if aspect < 0.4 or aspect > 2.5:
            return None, None

        # Compute centroid
        M = cv2.moments(c)
        if M["m00"] == 0:
            return None, None

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        palm_center = (cx, cy)

        # Draw on frame
        cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)
        cv2.circle(frame, (cx, cy), 8, (0, 0, 255), -1)

        # Build approximate 21 landmarks from contour and fingertip candidates
        fingers = self._get_fingertips(c, palm_center, w, h)
        landmarks = self._approximate_landmarks(fingers, palm_center, w, h)

        # Draw landmarks for debug
        for lm in landmarks:
            px = int(lm.x * w)
            py = int(lm.y * h)
            cv2.circle(frame, (px, py), 3, (255, 255, 0), -1)

        return frame, SimpleLandmarksContainer([(lm.x, lm.y) for lm in landmarks])

    def detect_hands(self, frame):
        if self.mode == "tasks":
            return self._mediapipe_detect(frame)
        else:  # opencv
            result_frame, landmarks = self._opencv_detect(frame)
            return result_frame if result_frame is not None else frame, landmarks
