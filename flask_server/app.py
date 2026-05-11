# Flask
from flask import Flask, render_template

# SocketIO
from flask_socketio import SocketIO

# Focus Mode
from control.focus_mode import FocusMode


# 建立 Flask
app = Flask(__name__)


# 建立 SocketIO
socketio = SocketIO(

    app,

    async_mode='threading',

    cors_allowed_origins="*"

)


# 建立 Focus Mode
focus_mode = FocusMode()


# 首頁
@app.route('/')

def home():

    return render_template("index.html")


# 接收 AI Client 手勢
@socketio.on("gesture")

def handle_gesture(data):

    # 取得手勢
    gesture = data["gesture"]

    print("收到手勢:", gesture)


    # 更新 Focus
    result = focus_mode.update(gesture)


    # 如果沒有事件
    if result is None:

        return


    print("事件:", result)


    # 傳送給前端
    socketio.emit(

        "focus_update",

        result

    )