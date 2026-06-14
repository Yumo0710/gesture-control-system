import cv2


class Webcam:
    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)

        # 設定較高解析度，讓手部關節偵測有足夠畫面細節。
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_FPS, 120)

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None

        # 鏡像畫面，讓使用者移動方向與螢幕顯示一致。
        return cv2.flip(frame, 1)

    def release(self):
        self.cap.release()
