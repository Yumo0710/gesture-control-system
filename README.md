# Gesture Control System

這是一個使用 Python、OpenCV、MediaPipe、Flask 與 Socket.IO 製作的手勢點餐系統。使用者可以用攝影機辨識手勢，在網頁菜單上切換餐點、調整數量，第一次 OK 手勢查看訂單明細，第二次 OK 手勢送出訂單。

- **Focus Mode**：左右滑切換餐點，上滑增加數量，下滑減少數量，OK 手勢進入確認流程。
- **Virtual Mouse Mode**：用手掌相對攝影機中心的位置控制滑鼠移動，並用拇指手勢觸發左鍵點擊。

## 專案架構

```text
gesture-control-system/
├─ main.py                         # 主程式，啟動 Flask、Socket.IO、攝影機與手勢流程
├─ virtual_mouse_control.py        # 單獨測試虛擬滑鼠控制
├─ requirements.txt                # Python 套件需求
├─ AGENTME.md                      # 專題協作與修改規範
├─ control/
│  ├─ focus_mode.py                # Focus Mode 的餐點索引與操作事件
│  └─ virtual_mouse.py             # Windows 滑鼠移動與點擊控制
├─ vision/
│  ├─ webcam.py                    # 攝影機影像讀取
│  ├─ hand_detector.py             # MediaPipe 手部偵測與 OpenCV fallback
│  └─ gesture_logic.py             # 手勢判斷：滑動、OK、模式切換、滑鼠點擊
├─ flask_server/
│  ├─ app.py                       # Flask 頁面與 Socket.IO 事件處理
│  ├─ templates/index.html         # 菜單、模式切換、手勢教學與訂單明細彈窗
│  └─ static/
│     ├─ style.css                 # 前端版面、卡片、確認區、教學與彈窗樣式
│     ├─ script.js                 # 前端模式、餐點數量、確認餐點與明細邏輯
│     └─ images/
│        ├─ gestures/              # 手勢教學 SVG 貼圖
│        └─ *.png                  # 餐點圖片
├─ tests/
│  └─ test_gesture_logic.py        # 手勢判斷單元測試
└─ vision_models/
   └─ hand_landmarker.task         # MediaPipe 模型檔，沒有時會嘗試下載或 fallback
```

## 執行流程

```text
Webcam
  -> HandDetector
  -> GestureLogic
  -> main.py
  -> Socket.IO
  -> Flask UI / FocusMode / VirtualMouse
```

1. `main.py` 啟動 Flask Server，並建立 Socket.IO Client。
2. `vision.webcam.Webcam` 讀取攝影機畫面。
3. `vision.hand_detector.HandDetector` 偵測手部 landmarks。
4. `vision.gesture_logic.GestureLogic` 判斷 `LEFT`、`RIGHT`、`PLUS`、`MINUS`、`CHECKOUT`、模式切換或滑鼠點擊。
5. Focus Mode 透過 Socket.IO 更新網頁菜單；Mouse Mode 透過 `control.virtual_mouse.VirtualMouse` 控制 Windows 滑鼠。

## 安裝

建議使用 Python 3.11。

```powershell
python -m venv .venv311
.\.venv311\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 執行

啟動完整系統：

```powershell
python main.py
```

啟動後開啟：

```text
http://localhost:5000
```

單獨測試虛擬滑鼠：

```powershell
python virtual_mouse_control.py
```

按 `Q` 或 `Esc` 可關閉 OpenCV 視窗。

## 控制模式

- 張開手掌停留約 1 秒：在 Focus Mode 與 Virtual Mouse Mode 之間切換。
- 鍵盤測試：按 `F` 切到 Focus Mode，按 `M` 切到 Virtual Mouse Mode。

## 手勢操作

- 左右滑：切換目前聚焦的餐點卡片。
- 上滑：增加目前餐點數量。
- 下滑：減少目前餐點數量。
- OK 手勢：第一次聚焦下方「確認餐點」並打開訂單明細；明細開啟後再 OK 一次送出訂單。
- Mouse Mode 中手掌偏移：控制滑鼠游標。
- Mouse Mode 中拇指點擊手勢：觸發滑鼠左鍵。

## 確認餐點

- `確認餐點` 按鈕獨立放在菜單下方，不會跟餐點卡片混在同一個 Focus 循環。
- Focus Mode 只在 5 個餐點間左右切換。
- 第一次比出 OK 手勢時，前端會高亮 `確認餐點`，並跳出訂單明細彈窗。
- 訂單明細已開啟時，再比一次 OK 手勢會送出訂單。
- 鍵盤可按 `C` 或 `Enter` 測試確認餐點，按 `Esc` 關閉明細。

## 期末報告輸出

- `reports/gesture_control_system_final_report.pptx`：符合評分規範的期末報告簡報，包含專題完整度、技術降維、測試結果、可能問答與分工。
- `reports/gesture_control_system_speaker_notes.md`：逐頁講稿、可能問答回答，以及依模組分區的程式碼註解文字稿。
- `reports/assets/gesture_cover.png`：使用 imagegen 產生的簡報封面主視覺。

## 測試

```powershell
python -m compileall .
python -m unittest discover -s tests
```

若修改 `main.py`、`flask_server/` 或 Socket.IO 相關流程，還需要開啟 `http://localhost:5000` 確認模式切換、手勢教學、菜單數量與訂單明細可正常運作。

## 修改原則

- 每次修改都要新增或整理必要的中文註解，讓組員能讀懂關鍵邏輯。
- 每次更新完成後，都要重新檢查專案架構，並同步整理 README。
- 不任意搬動資料夾或重命名檔案，除非能明確降低混亂並確認引用路徑一起更新。
- 修改後至少執行 `python -m compileall .`，並在有測試時執行 `python -m unittest discover -s tests`。
- 若修改前端或 Socket.IO 流程，要確認 Flask 首頁能正常渲染。
