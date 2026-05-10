import cv2


class Webcam:

    def __init__(self, camera_index=0):

        self.cap = cv2.VideoCapture(camera_index)

        # 設定解析度
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        # 設定 FPS
        self.cap.set(cv2.CAP_PROP_FPS, 120)

    def get_frame(self):

        ret, frame = self.cap.read()

        if not ret:
            return None

        # 左右翻轉
        frame = cv2.flip(frame, 1)

        return frame

    def release(self):

        self.cap.release()