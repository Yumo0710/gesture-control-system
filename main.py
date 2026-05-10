import cv2

from vision.webcam import Webcam
from vision.hand_detector import HandDetector
from vision.gesture_logic import GestureLogic

webcam = Webcam()

detector = HandDetector()

gesture_logic = GestureLogic()

while True:

    frame = webcam.get_frame()

    if frame is None:
        break

    # 手部偵測
    frame, hand_landmarks = detector.detect_hands(frame)

    # 如果有偵測到手
    if hand_landmarks:

        # 左右滑動
        swipe_gesture = gesture_logic.detect_swipe(hand_landmarks)

        if swipe_gesture:
            print(swipe_gesture)

        # 大拇指上下
        thumb_gesture = gesture_logic.detect_thumb(hand_landmarks)

        if thumb_gesture:
            print(thumb_gesture)

    cv2.imshow("Webcam", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

webcam.release()

cv2.destroyAllWindows()