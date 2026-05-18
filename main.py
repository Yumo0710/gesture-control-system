import cv2
import time

# 多執行緒
import threading

# SocketIO Client
import socketio

from vision.webcam import Webcam
from vision.hand_detector import HandDetector
from vision.gesture_logic import GestureLogic

# Flask
from flask_server.app import app
from flask_server.app import socketio as flask_socketio


# Flask Thread
def run_flask():

    flask_socketio.run(

        app,

        host='0.0.0.0',

        port=5000,

        debug=False,

        allow_unsafe_werkzeug=True
    )


# 啟動 Flask Thread
flask_thread = threading.Thread(

    target=run_flask,

    daemon=True
)

flask_thread.start()


# 等 Flask 啟動
time.sleep(2)


# 建立 SocketIO Client
sio = socketio.Client()


# 連接 Flask Server
sio.connect(

    "http://localhost:5000",

    transports=['websocket']

)


print("已連接 Flask Server")


# Webcam
webcam = Webcam()

# Hand Detector
detector = HandDetector()

# Gesture Logic
gesture_logic = GestureLogic()


while True:

    # 取得畫面
    frame = webcam.get_frame()

    if frame is None:
        break


    # 手部偵測
    frame, hand_landmarks = detector.detect_hands(frame)

    gesture = None

    # 使用特徵點姿勢邏輯辨識固定手勢，讓控制方式符合目前點餐頁需求。
    if hand_landmarks:

        gesture = gesture_logic.detect_gesture(hand_landmarks)

        if gesture:

            print("Gesture:", gesture)


    # 如果有手勢
    if gesture:

        # 發送給 Flask Server
        sio.emit("gesture", {

            "gesture": gesture

        })


    # 顯示畫面
    cv2.imshow("Webcam", frame)


    # Q 離開
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# 關閉 Webcam
webcam.release()

# 關閉 OpenCV
cv2.destroyAllWindows()
