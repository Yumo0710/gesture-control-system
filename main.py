import os
import cv2
import time

# 多執行緒
import threading
import sys
import tkinter as tk
from tkinter import messagebox

# Ensure we run inside the project virtual environment if available.
project_venv = os.path.abspath(os.path.join(os.path.dirname(__file__), ".venv311", "Scripts", "python.exe"))
if os.path.exists(project_venv) and os.path.normcase(sys.executable) != os.path.normcase(project_venv):
    print("Re-launching with project virtualenv:", project_venv)
    os.execv(project_venv, [project_venv] + sys.argv)

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
sio_connected = False
try:
    sio.connect(
        "http://localhost:5000",
        transports=['websocket']
    )
    sio_connected = True
    print("SocketIO connected via websocket")
except Exception as e:
    print("WebSocket transport failed, falling back to polling:", e)
    try:
        sio.connect("http://localhost:5000")
        sio_connected = True
        print("SocketIO connected via polling")
    except Exception as e2:
        print("SocketIO connection failed:", e2)
        raise


print("已連接 Flask Server")
print("Python executable:", sys.executable)
print("Python version:", sys.version)


# Webcam
webcam = Webcam()

# Hand Detector
try:
    detector = HandDetector(require_mediapipe=True)
except ImportError as e:
    print(e)
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "MediaPipe Initialization Failed",
        "MediaPipe 初始化失敗，請重新啟動程式後重試。"
    )
    root.destroy()
    sys.exit(1)

# Gesture Logic
gesture_logic = GestureLogic()

# Virtual Mouse
virtual_mouse = VirtualMouse()

# 目前控制模式
current_mode = "focus"

# 預先建立 Webcam 視窗
cv2.namedWindow("Webcam", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Webcam", 1280, 720)
window_opened = True

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


    # 如果有偵測到手，先計算 palm center (nx, ny)，並在左上顯示 xy
    if hand_landmarks:
        # Compute palm center from landmarks when available.
        palm_indices = [0, 1, 2, 5, 9, 13, 17]

        xs = []
        ys = []
        for i in palm_indices:
            if i < len(hand_landmarks.landmark):
                xs.append(hand_landmarks.landmark[i].x)
                ys.append(hand_landmarks.landmark[i].y)

        if xs and ys:
            nx = sum(xs) / len(xs)
            ny = sum(ys) / len(ys)
        else:
            # fallback to index tip
            p = hand_landmarks.landmark[8]
            nx, ny = p.x, p.y

        # 以畫面中心為原點的座標 (中心 = 0.00,0.00)
        ox = nx - 0.5
        oy = ny - 0.5

        # 顯示中心座標在左上，並畫中心十字與從中心到掌心的指示線
        cv2.putText(frame, f"cx:{ox:+.2f} cy:{oy:+.2f}", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        h, w = frame.shape[:2]
        cx_px = int(w * 0.5)
        cy_px = int(h * 0.5)
        palm_px = (int(nx * w), int(ny * h))

        # center crosshair
        cv2.line(frame, (cx_px - 10, cy_px), (cx_px + 10, cy_px), (200, 200, 200), 1)
        cv2.line(frame, (cx_px, cy_px - 10), (cx_px, cy_px + 10), (200, 200, 200), 1)

        # line from center to palm
        cv2.line(frame, (cx_px, cy_px), palm_px, (0, 255, 255), 1)

        if current_mode == "mouse":
            # center-based offset (-0.5 .. 0.5)
            ox = nx - 0.5
            oy = ny - 0.5

            # deadzone (no movement when close to center)
            deadzone = 0.12

            # max pixels per frame
            max_speed = 80

            def compute_speed(offset):
                mag = abs(offset) - deadzone
                if mag <= 0:
                    return 0
                norm = mag / (0.5 - deadzone)
                norm = max(0.0, min(1.0, norm))
                return norm * max_speed * (1 if offset > 0 else -1)

            dx = compute_speed(ox)
            dy = compute_speed(oy)

            # apply movement (note: positive oy -> palm below center -> move down)
            x, y = virtual_mouse.move_by(dx, dy)

            click = gesture_logic.detect_mouse_click(hand_landmarks)
            if click:
                virtual_mouse.click_left()
                cv2.putText(frame, "CLICK", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            cv2.putText(frame, f"Vel: {int(dx)},{int(dy)}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

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
                sio.emit("gesture", {"gesture": gesture})


    # 顯示畫面
    try:
        if cv2.getWindowProperty("Webcam", cv2.WND_PROP_VISIBLE) < 1:
            break
    except Exception:
        break

    cv2.imshow("Webcam", frame)

    # Q 或 Esc 離開
    k = cv2.waitKey(1)
    if k != -1 and (k & 0xFF == ord('q') or k & 0xFF == 27):
        break


# 關閉 Webcam
webcam.release()

# 關閉 OpenCV
cv2.destroyAllWindows()