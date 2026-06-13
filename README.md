# Gesture Control System 手勢控制系統

本專案為基於 Python 與電腦視覺的即時手勢控制系統。

## 使用技術

- Python
- Flask
- WebSocket
- OpenCV
- MediaPipe

## 專案目標

透過攝影機辨識手勢，
並將辨識結果轉換成控制指令。

## 系統架構

Camera
↓
MediaPipe
↓
Gesture Detection
↓
Flask Server
↓
Control System

## 控制模式

目前系統提供兩種控制方式：

### 1. Focus Mode（焦點控制）

透過焦點選中商品，
並使用手勢進行左右切換與確認操作。

目前開發階段使用鍵盤模擬控制：

- ← / → ：切換商品
- Enter ：加入商品
- Backspace ：減少商品

未來將結合 MediaPipe 手勢辨識，
以手勢取代鍵盤輸入。


### 2. Virtual Mouse Mode（虛擬滑鼠）

透過即時手部追蹤，
取得手部座標位置。

系統會根據手部座標：

- 移動虛擬游標
- 判斷目前選中商品
- 執行點擊操作

已新增 `virtual_mouse_control.py` 範例，可直接使用攝影機手指座標移動 Windows 滑鼠游標。

使用方式：在專案根目錄執行 `python virtual_mouse_control.py`。

此模式目前為後續開發目標。

## 開發進度

- [✅] Git 開發環境
- [✅] Flask 即時控制
- [✅] WebSocket
- [ ] OpenCV
- [ ] MediaPipe