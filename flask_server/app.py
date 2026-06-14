from flask import Flask, render_template
from flask_socketio import SocketIO

from control.focus_mode import FocusMode


# 建立 Flask 應用，專門提供菜單頁面與 Socket.IO 事件。
app = Flask(__name__)


# 使用 threading 模式，避免專題展示時還需要額外安裝 eventlet/gevent。
socketio = SocketIO(
    app,
    async_mode="threading",
    cors_allowed_origins="*",
)


# FocusMode 只管理 5 個餐點；確認餐點改由 OK 手勢獨立觸發。
focus_mode = FocusMode(item_count=5)

# 目前系統模式：focus 控制菜單，mouse 控制滑鼠。
current_mode = "focus"


@app.route("/")
def home():
    # 回傳主要操作頁面，前端會透過 Socket.IO 接收手勢更新。
    return render_template("index.html")


@socketio.on("mode_change")
def handle_mode_change(data):
    global current_mode

    mode = data.get("mode")
    if mode not in ["focus", "mouse"]:
        return

    current_mode = mode
    print("控制模式已切換:", current_mode)
    socketio.emit("mode_changed", {"mode": current_mode})


@socketio.on("gesture")
def handle_gesture(data):
    # 接收主程式送來的手勢結果，只有 Focus Mode 會更新網頁菜單。
    gesture = data.get("gesture")
    if not gesture:
        return

    print("收到手勢:", gesture, "mode:", current_mode)
    if current_mode != "focus":
        return

    # 將手勢轉成 Focus Mode 的 UI 更新指令。
    result = focus_mode.update(gesture)
    if result is None:
        return

    print("Focus 更新:", result)
    socketio.emit("focus_update", result)
