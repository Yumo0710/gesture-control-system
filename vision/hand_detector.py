import math
import os
import urllib.request

import cv2


HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
]


class SimpleLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class SimpleLandmarksContainer:
    def __init__(self, landmarks):
        # 統一回傳格式，讓後續 GestureLogic 不需要知道目前使用哪個偵測器。
        self.landmark = [SimpleLandmark(x, y) for x, y in landmarks]


class HandDetector:
    def __init__(self, require_mediapipe=True, model_dir=None):
        self.mode = None
        self.hand_detector = None
        self.mp_hands = None

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.model_dir = model_dir or os.path.join(project_root, "vision_models")

        self._setup_tasks_detector()
        if self.mode is None:
            self._setup_solutions_detector()

        if self.mode is None:
            if require_mediapipe:
                raise ImportError(
                    "MediaPipe could not be initialized. Please install requirements.txt and use Python 3.11."
                )
            self.mode = "opencv"
            print("Using OpenCV fallback detector mode.")

    def _setup_tasks_detector(self):
        try:
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            os.makedirs(self.model_dir, exist_ok=True)
            model_path = os.path.join(self.model_dir, "hand_landmarker.task")

            if not os.path.exists(model_path):
                self._download_model(model_path)

            if not os.path.exists(model_path):
                return

            # Tasks API 偵測準確度較好，模型檔存在時優先使用。
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
        except Exception as error:
            print(f"HandLandmarker setup failed: {error}")
            self.mode = None
            self.hand_detector = None

    def _setup_solutions_detector(self):
        try:
            import mediapipe as mp

            self.mp_hands = mp.solutions.hands
            self.hand_detector = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7,
            )
            self.mode = "solutions"
            print("MediaPipe Solutions Hands mode: OK")
        except Exception as error:
            print(f"MediaPipe Solutions Hands setup failed: {error}")
            self.mode = None
            self.hand_detector = None

    def _download_model(self, model_path):
        print(f"Downloading hand_landmarker.task to {model_path}...")
        urls = [
            "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
            "https://storage.googleapis.com/mediapipe-assets/hand_landmarker.task",
        ]

        for url in urls:
            try:
                urllib.request.urlretrieve(url, model_path)
                print(f"Download complete from {url}")
                return
            except Exception as error:
                print(f"Download from {url} failed: {error}")

        print("All model download URLs failed. Trying MediaPipe Solutions fallback.")

    def _draw_landmarks(self, frame, landmarks, color=(0, 255, 0)):
        h, w = frame.shape[:2]

        for x, y in landmarks:
            cv2.circle(frame, (int(x * w), int(y * h)), 3, color, -1)

        for start, end in HAND_CONNECTIONS:
            if start < len(landmarks) and end < len(landmarks):
                x1, y1 = landmarks[start]
                x2, y2 = landmarks[end]
                cv2.line(frame, (int(x1 * w), int(y1 * h)), (int(x2 * w), int(y2 * h)), color, 1)

    def _tasks_detect(self, frame):
        try:
            import mediapipe as mp

            # MediaPipe 0.10.x 使用公開的 mp.Image，避免依賴不穩定的內部模組路徑。
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = self.hand_detector.detect(mp_image)

            if not result.hand_landmarks:
                return frame, None

            landmarks = [(lm.x, lm.y) for lm in result.hand_landmarks[0]]
            self._draw_landmarks(frame, landmarks)
            return frame, SimpleLandmarksContainer(landmarks)
        except Exception as error:
            print(f"MediaPipe Tasks detection error: {error}")
            return frame, None

    def _solutions_detect(self, frame):
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hand_detector.process(rgb_frame)

            if not result.multi_hand_landmarks:
                return frame, None

            landmarks = [(lm.x, lm.y) for lm in result.multi_hand_landmarks[0].landmark]
            self._draw_landmarks(frame, landmarks)
            return frame, SimpleLandmarksContainer(landmarks)
        except Exception as error:
            print(f"MediaPipe Solutions detection error: {error}")
            return frame, None

    def _get_fingertips(self, contour, palm_center, w, h):
        hull = cv2.convexHull(contour, returnPoints=True)
        if hull is None or len(hull) == 0:
            return []

        hull_points = [tuple(point[0]) for point in hull]
        candidates = []
        palm_x, palm_y = palm_center

        for index, current in enumerate(hull_points):
            previous = hull_points[index - 1]
            following = hull_points[(index + 1) % len(hull_points)]

            # 指尖通常位於掌心上方，先排除掌心下方的輪廓點。
            if current[1] > palm_y + 20:
                continue

            vector_a = (previous[0] - current[0], previous[1] - current[1])
            vector_b = (following[0] - current[0], following[1] - current[1])
            mag_a = math.hypot(vector_a[0], vector_a[1])
            mag_b = math.hypot(vector_b[0], vector_b[1])
            if mag_a == 0 or mag_b == 0:
                continue

            dot = vector_a[0] * vector_b[0] + vector_a[1] * vector_b[1]
            angle = math.acos(max(-1.0, min(1.0, dot / (mag_a * mag_b))))
            distance = math.hypot(current[0] - palm_x, current[1] - palm_y)

            if angle < 1.3 and distance > 0.08 * max(w, h):
                candidates.append((current[0], current[1], distance))

        filtered = []
        for x, y, distance in sorted(candidates, key=lambda item: item[2], reverse=True):
            if not any(math.hypot(x - fx, y - fy) < 25 for fx, fy, _ in filtered):
                filtered.append((x, y, distance))

        return [(x, y) for x, y, _ in filtered[:5]]

    def _approximate_landmarks(self, tips, palm_center, w, h):
        palm_x, palm_y = palm_center
        tips = sorted(tips, key=lambda point: (point[1], point[0]))

        while len(tips) < 5:
            tips.append((palm_x, palm_y - int(0.15 * h)))

        thumb_tip = max(tips, key=lambda point: abs(point[0] - palm_x))
        remaining = [point for point in tips if point != thumb_tip]
        remaining = sorted(remaining, key=lambda point: point[0])
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

        while len(landmarks) < 21:
            landmarks.append(SimpleLandmark(palm_x / w, palm_y / h))

        return landmarks[:21]

    def _opencv_detect(self, frame):
        h, w = frame.shape[:2]
        frame_area = h * w

        # OpenCV 備援偵測使用膚色遮罩，只在 MediaPipe 不可用時才會使用。
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask_hsv = cv2.inRange(hsv, (0, 30, 60), (20, 150, 255))

        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        mask_ycrcb = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127))

        mask = cv2.bitwise_and(mask_hsv, mask_ycrcb)
        mask = cv2.GaussianBlur(mask, (7, 7), 0)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return frame, None

        contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contour)
        if area < 1500 or area > 0.20 * frame_area:
            return frame, None

        x, y, box_width, box_height = cv2.boundingRect(contour)
        box_area = box_width * box_height
        extent = area / box_area if box_area > 0 else 0
        aspect = box_width / box_height if box_height > 0 else 0

        if extent < 0.25 or extent > 0.95:
            return frame, None
        if box_height > 0.8 * h or box_width > 0.8 * w:
            return frame, None
        if aspect < 0.4 or aspect > 2.5:
            return frame, None

        moments = cv2.moments(contour)
        if moments["m00"] == 0:
            return frame, None

        palm_center = (int(moments["m10"] / moments["m00"]), int(moments["m01"] / moments["m00"]))
        cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
        cv2.circle(frame, palm_center, 8, (0, 0, 255), -1)

        fingertips = self._get_fingertips(contour, palm_center, w, h)
        landmark_objects = self._approximate_landmarks(fingertips, palm_center, w, h)
        landmarks = [(landmark.x, landmark.y) for landmark in landmark_objects]
        self._draw_landmarks(frame, landmarks, color=(255, 255, 0))
        return frame, SimpleLandmarksContainer(landmarks)

    def detect_hands(self, frame):
        if self.mode == "tasks":
            return self._tasks_detect(frame)
        if self.mode == "solutions":
            return self._solutions_detect(frame)
        return self._opencv_detect(frame)
