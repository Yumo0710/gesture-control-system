import os
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

import cv2
import socketio

from control.virtual_mouse import VirtualMouse
from flask_server.app import app
from flask_server.app import socketio as flask_socketio
from vision.gesture_logic import GestureLogic
from vision.hand_detector import HandDetector
from vision.webcam import Webcam


PROJECT_VENV = os.path.abspath(os.path.join(os.path.dirname(__file__), ".venv311", "Scripts", "python.exe"))


# 若專案內已有指定虛擬環境，優先用它重新啟動，降低套件版本不一致的風險。
if os.path.exists(PROJECT_VENV) and os.path.normcase(sys.executable) != os.path.normcase(PROJECT_VENV):
    print("Re-launching with project virtualenv:", PROJECT_VENV)
    os.execv(PROJECT_VENV, [PROJECT_VENV] + sys.argv)


def run_flask():
    # Flask 跑在背景執行緒，主執行緒保留給 OpenCV 攝影機迴圈。
    flask_socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True,
    )


def connect_socketio_client():
    # 主程式使用 Socket.IO Client 把手勢事件送回 Flask Server。
    client = socketio.Client()

    try:
        client.connect("http://localhost:5000", transports=["websocket"])
        print("SocketIO connected via websocket")
    except Exception as error:
        print("WebSocket transport failed, falling back to polling:", error)
        client.connect("http://localhost:5000")
        print("SocketIO connected via polling")

    return client


def initialize_detector():
    try:
        return HandDetector(require_mediapipe=True)
    except ImportError as error:
        print(error)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "MediaPipe Initialization Failed",
            "MediaPipe 無法初始化，請確認已安裝 requirements.txt 內的套件，並使用支援的 Python 版本。",
        )
        root.destroy()
        sys.exit(1)


def get_palm_center(hand_landmarks):
    # 使用掌心附近的多個點平均，讓滑鼠移動比單一指尖更穩定。
    palm_indices = [0, 1, 2, 5, 9, 13, 17]
    xs = []
    ys = []

    for index in palm_indices:
        if index < len(hand_landmarks.landmark):
            xs.append(hand_landmarks.landmark[index].x)
            ys.append(hand_landmarks.landmark[index].y)

    if xs and ys:
        return sum(xs) / len(xs), sum(ys) / len(ys)

    # 若 landmarks 不完整，退回食指指尖座標，避免流程直接中斷。
    fallback = hand_landmarks.landmark[8]
    return fallback.x, fallback.y


def compute_cursor_speed(offset, deadzone=0.12, max_speed=80):
    # 死區可避免手在畫面中心附近微抖時造成游標漂移。
    magnitude = abs(offset) - deadzone
    if magnitude <= 0:
        return 0

    normalized = magnitude / (0.5 - deadzone)
    normalized = max(0.0, min(1.0, normalized))
    return normalized * max_speed * (1 if offset > 0 else -1)


def draw_palm_debug(frame, nx, ny):
    # 畫出畫面中心與掌心連線，方便展示時校準手的位置。
    h, w = frame.shape[:2]
    cx_px = int(w * 0.5)
    cy_px = int(h * 0.5)
    palm_px = (int(nx * w), int(ny * h))

    cv2.line(frame, (cx_px - 10, cy_px), (cx_px + 10, cy_px), (200, 200, 200), 1)
    cv2.line(frame, (cx_px, cy_px - 10), (cx_px, cy_px + 10), (200, 200, 200), 1)
    cv2.line(frame, (cx_px, cy_px), palm_px, (0, 255, 255), 1)


def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # 等待 Flask 完成啟動，避免 Socket.IO Client 太早連線失敗。
    time.sleep(2)
    sio = connect_socketio_client()

    print("已連線到 Flask Server")
    print("Python executable:", sys.executable)
    print("Python version:", sys.version)

    webcam = Webcam()
    detector = initialize_detector()
    gesture_logic = GestureLogic()
    virtual_mouse = VirtualMouse()
    current_mode = "focus"

    cv2.namedWindow("Webcam", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Webcam", 1280, 720)

    @sio.on("mode_changed")
    def on_mode_changed(data):
        nonlocal current_mode
        current_mode = data.get("mode", "focus")
        print("收到模式切換:", current_mode)

    def switch_mode_by_gesture():
        # 手勢切換直接走和前端按鈕相同的 Socket.IO 事件，確保前後端狀態一致。
        next_mode = "mouse" if current_mode == "focus" else "focus"
        sio.emit("mode_change", {"mode": next_mode})
        return next_mode

    while True:
        frame = webcam.get_frame()
        if frame is None:
            break

        frame, hand_landmarks = detector.detect_hands(frame)

        if hand_landmarks:
            nx, ny = get_palm_center(hand_landmarks)
            ox = nx - 0.5
            oy = ny - 0.5

            cv2.putText(frame, f"cx:{ox:+.2f} cy:{oy:+.2f}", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            draw_palm_debug(frame, nx, ny)

            # 張開手掌並停住約 1 秒即可切換 Focus / Mouse，兩種模式都可使用。
            if gesture_logic.detect_mode_switch(hand_landmarks):
                next_mode = switch_mode_by_gesture()
                cv2.putText(frame, f"MODE -> {next_mode.upper()}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
                cv2.imshow("Webcam", frame)
                cv2.waitKey(1)
                continue

            if current_mode == "mouse":
                dx = compute_cursor_speed(ox)
                dy = compute_cursor_speed(oy)
                virtual_mouse.move_by(dx, dy)

                if gesture_logic.detect_mouse_click(hand_landmarks):
                    virtual_mouse.click_left()
                    cv2.putText(frame, "CLICK", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                cv2.putText(frame, f"Vel: {int(dx)},{int(dy)}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                gesture = gesture_logic.detect_swipe(hand_landmarks) or gesture_logic.detect_thumb(hand_landmarks)
                if gesture:
                    print("Gesture:", gesture)
                    sio.emit("gesture", {"gesture": gesture})

        try:
            if cv2.getWindowProperty("Webcam", cv2.WND_PROP_VISIBLE) < 1:
                break
        except Exception:
            break

        cv2.imshow("Webcam", frame)

        key = cv2.waitKey(1)
        if key != -1 and (key & 0xFF == ord("q") or key & 0xFF == 27):
            break

    webcam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
