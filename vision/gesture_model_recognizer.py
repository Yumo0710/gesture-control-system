from pathlib import Path
import time

import cv2
import mediapipe as mp


class GestureModelRecognizer:

    def __init__(
        self,
        model_path=None,
        min_confidence=0.65,
        stable_frames=3,
        trigger_cooldown=0.6
    ):

        project_root = Path(__file__).resolve().parents[1]

        self.model_path = Path(model_path) if model_path else (
            project_root / "models" / "gesture_recognizer.task"
        )

        self.min_confidence = min_confidence

        self.stable_frames = stable_frames

        self.trigger_cooldown = trigger_cooldown

        self.recognizer = None

        self.last_label = None

        self.last_score = 0

        self.pending_label = None

        self.pending_count = 0

        self.last_trigger_time = 0

        # 使用 MediaPipe 預訓練 Gesture Recognizer，避免只依賴 2D 座標閾值造成誤判。
        self._load_model()


    def _load_model(self):

        if not self.model_path.exists():

            print(
                "找不到預訓練手勢模型，將使用原本 landmarks 規則：",
                self.model_path
            )

            return

        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        # Windows 環境下 MediaPipe 可能會誤解析磁碟機路徑，因此改用 bytes 載入模型。
        model_buffer = self.model_path.read_bytes()

        base_options = python.BaseOptions(
            model_asset_buffer=model_buffer
        )

        options = vision.GestureRecognizerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6
        )

        self.recognizer = vision.GestureRecognizer.create_from_options(options)

        print("已載入預訓練手勢模型：", self.model_path)


    def is_available(self):

        return self.recognizer is not None


    def recognize(self, frame):

        if not self.is_available():

            return None

        # MediaPipe Task API 需要 RGB 影像，因此先從 OpenCV 的 BGR 格式轉換。
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        result = self.recognizer.recognize(mp_image)

        if not result.gestures:

            self.last_label = None

            self.last_score = 0

            return None

        category = result.gestures[0][0]

        self.last_label = category.category_name

        self.last_score = category.score

        if category.score < self.min_confidence:

            self._reset_pending()

            return None

        return self._get_stable_gesture(category.category_name)


    def _get_stable_gesture(self, label):

        # 同一個模型標籤必須連續出現數幀，避免單幀誤判直接觸發控制事件。
        if label == self.pending_label:

            self.pending_count += 1

        else:

            self.pending_label = label

            self.pending_count = 1

        if self.pending_count < self.stable_frames:

            return None

        current_time = time.time()

        if current_time - self.last_trigger_time < self.trigger_cooldown:

            return None

        gesture = self._map_model_label(label)

        if gesture:

            self.last_trigger_time = current_time

            self._reset_pending()

        return gesture


    def _reset_pending(self):

        self.pending_label = None

        self.pending_count = 0


    def _map_model_label(self, label):

        # 將模型輸出的英文標籤轉成專案既有控制手勢，保留 main.py -> Flask -> 前端的資料流。
        gesture_map = {
            "Thumb_Up": "PLUS",
            "Thumb_Down": "MINUS",
            "Closed_Fist": "SELECT",
            "Victory": "LEFT",
            "Open_Palm": "RIGHT",
            "Left": "LEFT",
            "Right": "RIGHT",
            "Swipe_Left": "LEFT",
            "Swipe_Right": "RIGHT"
        }

        return gesture_map.get(label)


    def draw_status(self, frame):

        if not self.last_label:

            return frame

        text = f"Model: {self.last_label} ({self.last_score:.2f})"

        # 在畫面左上角顯示模型判斷結果，方便調整信心分數與觀察誤判來源。
        cv2.putText(
            frame,
            text,
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )

        return frame


    def close(self):

        if self.recognizer:

            self.recognizer.close()
