import cv2
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
                # Create HandLandmarker without running_mode (IMAGE mode is default)
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

    def _opencv_detect(self, frame):
        # Simple skin-like color threshold in HSV to find largest contour
        # Skin detection: combine HSV and YCrCb thresholds for robustness
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_hsv = (0, 30, 60)
        upper_hsv = (20, 150, 255)
        mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)

        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        lower_ycrcb = (0, 133, 77)
        upper_ycrcb = (255, 173, 127)
        mask_ycrcb = cv2.inRange(ycrcb, lower_ycrcb, upper_ycrcb)

        mask = cv2.bitwise_and(mask_hsv, mask_ycrcb)
        # blur and morph
        mask = cv2.GaussianBlur(mask, (7, 7), 0)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None

        # largest contour
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        h, w = frame.shape[:2]
        frame_area = h * w

        # require minimal area and reject overly large blobs (likely full body)
        if area < 1500 or area > 0.20 * frame_area:
            return None, None

        M = cv2.moments(c)
        if M["m00"] == 0:
            return None, None

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        h, w = frame.shape[:2]
        nx = cx / w
        ny = cy / h

        # Basic bounding box checks
        x, y, bw, bh = cv2.boundingRect(c)
        bbox_area = bw * bh
        extent = float(area) / bbox_area if bbox_area > 0 else 0
        # expect a reasonably solid blob (palm), filter out long thin shapes
        if extent < 0.25 or extent > 0.95:
            return None, None

        # bounding box relative size checks: palm shouldn't occupy majority of frame
        if bh > 0.6 * h or bw > 0.6 * w:
            return None, None

        aspect = float(bw) / bh if bh > 0 else 0
        if aspect < 0.4 or aspect > 2.5:
            return None, None

        # Convexity defects (expect multiple between fingers for open palm)
        hull = cv2.convexHull(c, returnPoints=False)
        defects = None
        defect_count = 0
        try:
            if hull is not None and len(hull) > 3:
                defects = cv2.convexityDefects(c, hull)
                if defects is not None:
                    # count defects with sufficient depth
                    for i in range(defects.shape[0]):
                        s, e, f, depth = defects[i, 0]
                        # depth is multiplied by 256 in OpenCV; normalize by area
                        if depth / 256.0 > 0.01 * (bw + bh):
                            defect_count += 1
        except Exception:
            defect_count = 0

        # require at least 2-3 defects for an open palm; otherwise likely not a palm
        if defect_count < 2:
            return None, None

        # solidity: area / convex hull area (expect fairly solid shape)
        hull_pts = cv2.convexHull(c)
        hull_area = cv2.contourArea(hull_pts) if hull_pts is not None else 0
        solidity = float(area) / hull_area if hull_area > 0 else 0
        if solidity < 0.4:
            return None, None

        # Draw
        cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)
        cv2.circle(frame, (cx, cy), 8, (0, 0, 255), -1)

        # Create a fake landmarks container where landmark 8 is centroid
        landmarks = [(nx, ny)] * 21
        return frame, SimpleLandmarksContainer(landmarks)

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

    def detect_hands(self, frame):
        if self.mode == "tasks":
            return self._mediapipe_detect(frame)
        else:  # opencv
            result_frame, landmarks = self._opencv_detect(frame)
            return result_frame if result_frame is not None else frame, landmarks
