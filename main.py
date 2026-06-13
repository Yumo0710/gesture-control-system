import cv2
import time

# 多執行緒
import threading

# SocketIO Client
import socketio

from vision.webcam import Webcam
from vision.hand_detector import HandDetector
from vision.gesture_logic import GestureLogic
from control.virtual_mouse import VirtualMouse

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

# Virtual Mouse
virtual_mouse = VirtualMouse()

# 目前控制模式
current_mode = "focus"


# 接收模式變更
@sio.on("mode_changed")

def on_mode_changed(data):

    global current_mode

    current_mode = data.get("mode", "focus")

    print("接收到模式變更：", current_mode)


while True:

    # 取得畫面
    frame = webcam.get_frame()

    if frame is None:
        break


    # 手部偵測
    frame, hand_landmarks = detector.detect_hands(frame)


    # 如果有偵測到手
    if hand_landmarks:

        if current_mode == "mouse":

            index_finger = hand_landmarks.landmark[8]

            x, y = virtual_mouse.move(index_finger.x, index_finger.y)

            cv2.putText(

                frame,

                f"Mouse: {x},{y}",

                (30, 40),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (0, 255, 0),

                2,

            )

        else:

            gesture = None


            # 左右滑動
            swipe_gesture = gesture_logic.detect_swipe(hand_landmarks)

            if swipe_gesture:

                gesture = swipe_gesture

                print("Swipe:", gesture)


            # 大拇指手勢
            thumb_gesture = gesture_logic.detect_thumb(hand_landmarks)

            if thumb_gesture:

                gesture = thumb_gesture

                print("Thumb:", gesture)


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