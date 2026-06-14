# AGENTME：手勢控制系統協作規範

這份文件記錄本專題給 AI Agent 與組員共同遵守的修改規則，目標是讓程式可以持續優化，但不因為隨意更動而變得難以維護。

## 專題目標

本專題是以攝影機手勢控制為核心的點餐系統，主要包含：

- 攝影機讀取與手部偵測。
- 手勢邏輯判斷，例如左右滑、上下滑、OK 確認、模式切換與滑鼠點擊。
- Flask 與 Socket.IO 即時更新網頁菜單。
- Focus Mode 點餐操作與 Virtual Mouse Mode 滑鼠操作。

## 修改規則

- 每次修改都要新增或整理必要的中文註解，特別是手勢判斷、模式切換、Socket.IO 與前端互動。
- 每次更新完成後，都要重新檢查專案架構，並同步整理 README。
- 不亂更動檔案名稱、資料夾位置或既有流程；如果真的需要整理，必須同時更新引用路徑與文件。
- 優化要以可讀性、穩定性、操作靈敏度與展示效果為優先。
- 修改後要確認程式仍可正常執行，至少執行 Python 語法編譯檢查。
- 若有測試，修改後要執行測試，避免手勢邏輯回歸。

## 驗證指令

每次修改後建議執行：

```powershell
python -m compileall .
python -m unittest discover -s tests
```

若修改 `main.py`、`flask_server/` 或 Socket.IO 流程，還需要人工確認：

- `python main.py` 可以啟動 Flask 與 OpenCV 視窗。
- 網頁可以開啟 `http://localhost:5000`。
- Focus Mode 與 Virtual Mouse Mode 能正常切換。
- 手勢教學、菜單數量、確認餐點與訂單明細符合目前需求。

## 資料夾分工

- `vision/`：攝影機、MediaPipe/OpenCV 偵測、手勢判斷。
- `control/`：Focus Mode 狀態與 Windows 滑鼠控制。
- `flask_server/`：Flask、Socket.IO、HTML、CSS、JavaScript 與圖片素材。
- `tests/`：單元測試，優先覆蓋手勢判斷。
- `main.py`：整合流程，不要塞入過多 UI 或手勢細節。

## 完成標準

- README 的架構與操作說明已更新。
- Python 編譯檢查通過。
- 相關測試通過。
- 前端頁面可正常渲染。
- 沒有留下不必要的暫存資料夾或 debug 輸出。
