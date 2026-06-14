# Gesture Control System

以 Python、OpenCV、MediaPipe、Flask 與 Socket.IO 建立的手勢控制系統。專案支援兩種操作模式：

- **Focus Mode**：用左右揮手切換餐點卡片，握拳進入數量調整狀態，再用拇指方向增加或減少數量。
- **Virtual Mouse Mode**：用手掌相對攝影機中心的位置控制滑鼠移動，並用拇指手勢觸發左鍵點擊。

## 新架構

```text
gesture-control-system/
├─ main.py                         # 主入口：啟動 Flask、Socket.IO、攝影機與手勢流程
├─ virtual_mouse_control.py        # 單獨測試虛擬滑鼠控制的入口
├─ requirements.txt                # Python 套件版本
├─ AGENTME.md                      # 專題協作與修改規範
├─ control/
│  ├─ focus_mode.py                # Focus Mode 狀態機與菜單索引控制
│  └─ virtual_mouse.py             # Windows 滑鼠移動與點擊封裝
├─ vision/
│  ├─ webcam.py                    # 攝影機讀取與畫面鏡像
│  ├─ hand_detector.py             # MediaPipe 手部偵測，失敗時可退回 OpenCV 偵測
│  └─ gesture_logic.py             # 揮手、握拳、拇指、點擊與模式切換手勢判斷
├─ flask_server/
│  ├─ app.py                       # Flask 頁面與 Socket.IO 事件處理
│  ├─ templates/index.html         # 菜單操作頁面，含模式切換與手勢貼圖教學
│  └─ static/
│     ├─ style.css                 # 前端樣式、響應式版面與教學貼圖對齊
│     ├─ script.js                 # 前端模式切換、快捷鍵、分類篩選與數量更新邏輯
│     └─ images/
│        ├─ gestures/              # 手勢教學 SVG 貼圖
│        └─ *.png                  # 菜單圖片素材
├─ tests/
│  └─ test_gesture_logic.py        # 手勢判斷的基本單元測試
└─ vision_models/
   └─ hand_landmarker.task         # MediaPipe 模型檔，若不存在會嘗試下載
```

## 系統流程

```text
Webcam
  -> HandDetector
  -> GestureLogic
  -> main.py
  -> Socket.IO
  -> Flask UI / FocusMode / VirtualMouse
```

1. `main.py` 啟動 Flask Server，並建立 Socket.IO Client 連回本機服務。
2. `vision.webcam.Webcam` 從攝影機取得影像。
3. `vision.hand_detector.HandDetector` 偵測手部關節點。
4. `vision.gesture_logic.GestureLogic` 將關節點轉成模式切換、`LEFT`、`RIGHT`、`PLUS`、`MINUS` 或滑鼠點擊。
5. Focus Mode 透過 Socket.IO 更新網頁菜單；Mouse Mode 透過 `control.virtual_mouse.VirtualMouse` 控制 Windows 游標。

## 安裝

建議使用 Python 3.11。

```powershell
python -m venv .venv311
.\.venv311\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 執行

完整系統：

```powershell
python main.py
```

啟動後開啟瀏覽器：

```text
http://localhost:5000
```

單獨測試虛擬滑鼠：

```powershell
python virtual_mouse_control.py
```

按 `Q` 或 `Esc` 可關閉 OpenCV 視窗。

## 模式切換

目前有三種切換方式：

- 張開手掌並停住約 1 秒：在 Focus Mode 與 Virtual Mouse 之間切換。
- 點擊網頁上方的 `Focus Mode` 或 `Virtual Mouse` 按鈕。
- 使用鍵盤快捷鍵：按 `F` 切到 Focus Mode，按 `M` 切到 Virtual Mouse。

手勢切換時，`main.py` 會送出 `mode_change`，後端收到後再廣播 `mode_changed`，讓網頁與 Python 主程式保持同一個模式。

## 手勢操作

- 張開手掌並停住約 1 秒：切換 Focus Mode / Virtual Mouse。
- 左右揮動食指：切換目前選取的餐點。
- 握拳：進入數量調整狀態。
- 拇指向上或向下：增加或減少目前餐點數量。
- Mouse Mode 中移動手掌：控制游標方向與速度。
- Mouse Mode 中拇指點擊手勢：觸發滑鼠左鍵。

## 驗證

```powershell
python -m compileall .
python -m unittest discover -s tests
```

若修改前端互動，請再開啟 `http://localhost:5000` 檢查模式切換、手勢貼圖教學與菜單狀態。

## 修改原則

- 每次修改程式邏輯時，需補上必要的中文註解，說明「為什麼這樣做」或「這段處理的目的」。
- 每次更新完成後，都要重新檢查專案架構，並同步整理 README，確保文件與實際程式一致。
- 優先修正可執行性、穩定性與可讀性，不做與本專題無關的大改。
- 修改後至少執行 `python -m compileall .`，確認 Python 檔案沒有語法錯誤。
- 若改到前端互動，需實際開啟 `http://localhost:5000` 檢查畫面與 Socket.IO 狀態。
