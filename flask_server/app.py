# Flask:
#   建立網站伺服器
#
# render_template:
#   用來讀取 HTML 頁面
from flask import Flask, render_template
from flask_socketio import SocketIO


# 建立 Flask 網站物件
#
# __name__ 代表目前這份 Python 檔案
#
# Flask 會根據這個位置
# 找到 templates / static 資料夾
app = Flask(__name__)

# 建立 SocketIO 物件
socketio = SocketIO(app)


# @加入特殊功能  app.route("/") == local/ 把local/ 網址登入給下方函式 
# 當有人進入此網址 就會執行下面函式
@app.route('/')

def home():

    # 讀取 templates 資料夾中的 HTML
    return render_template("index.html")


# 當網頁發送： socket.emit("menu_select", data)
# 觸發下列函式
@socketio.on('menu_select')

def handle_menu(data):

    # 在 Terminal 顯示資料
    print("選擇:", data)



if __name__ == '__main__':

    # 啟動 Flask 網站
    #
    # host='0.0.0.0'
    #   允許區域網路存取
    #
    # port=5000
    #   網站埠號
    socketio.run(app, host='0.0.0.0', port=5000)