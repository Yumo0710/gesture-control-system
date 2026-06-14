# Gesture Control System 期末報告文字稿

## 使用方式
- PPT 用於正式報告。
- 本文字稿包含逐頁講稿、可能問題與回答、程式碼分區註解文字稿。
- 報告時建議先講主流程，再講技術分區，最後用 Q&A 收尾。

## 逐頁講稿

### Slide 01｜Gesture Control System

本專題的目標是做出可以實際展示的手勢點餐系統。使用者不需要碰鍵盤滑鼠，就可以透過攝影機辨識手勢，在網頁菜單上切換餐點、調整數量，最後使用 OK 手勢確認訂單。

### Slide 02｜評分規範對應

這頁直接對應老師給的評分項目。我們的簡報不是只展示畫面，而是把需求、技術方法、測試結果、可能問題和分工都放進去，讓評審可以快速看到完整度。

### Slide 03｜專題動機與需求

我們的動機是把手勢辨識應用到點餐情境。這個題目不只是辨識手勢，還要能和網頁互動，所以系統需要同時處理影像、手勢邏輯、後端事件和前端 UI。

### Slide 04｜系統總體架構

整體流程是由攝影機開始，先取得影像，再由手部偵測器產生 landmarks。GestureLogic 負責把 landmarks 轉成高階手勢事件，最後透過 Socket.IO 更新網頁。這樣分層後，每個模組的責任都很清楚。

### Slide 05｜技術環境與工具

這頁說明技術棧。Python 負責影像與控制流程，MediaPipe 負責手部偵測，Flask 和 Socket.IO 負責把後端手勢即時傳到前端。前端則負責顯示菜單和訂單。

### Slide 06｜主要操作流程

使用者流程設計成兩種模式。Focus Mode 針對點餐，操作簡單明確；Mouse Mode 則讓使用者可以用手掌控制滑鼠。確認訂單採兩段式 OK，避免誤觸直接送出。

### Slide 07｜Focus Mode 設計

Focus Mode 的重點是降低操作複雜度。原本確認餐點如果混在菜單循環裡，使用者要切到最後一格才確認；現在改成 OK 手勢獨立確認，操作更自然。

### Slide 08｜手勢判斷邏輯

GestureLogic 是手勢辨識的核心。它不是直接做複雜模型分類，而是使用 landmarks 的幾何關係判斷，這樣比較容易解釋，也方便調整靈敏度。

### Slide 09｜Virtual Mouse Mode

虛擬滑鼠模式不是把手的位置直接映射到螢幕，而是依照偏移量產生移動速度，這樣比較像搖桿控制，也比較不容易突然跳動。

### Slide 10｜Webcam 與 HandDetector

影像偵測層的設計重點是穩定性。MediaPipe Tasks API 準確度較好，所以優先使用；如果環境或模型有問題，會嘗試其他方式，避免整個系統直接無法展示。

### Slide 11｜Flask 與 Socket.IO

Flask 和 Socket.IO 是後端與前端的橋梁。這樣主程式只需要送出手勢事件，網頁 UI 自己負責畫面變化，讓影像處理和前端顯示分工清楚。

### Slide 12｜前端 UI 與確認流程

前端設計的重點是讓展示者和觀眾都看得懂目前狀態。右側有手勢教學，底部有模式、狀態和總金額。確認流程獨立放在下方，可以避免和餐點混淆。

### Slide 13｜測試與驗證結果

我們用三層驗證：第一層是 Python 語法，第二層是手勢邏輯單元測試，第三層是 Flask 頁面渲染。這可以證明不是只有畫面做出來，而是核心流程也有檢查。

### Slide 14｜開發問題與解法

這頁可以講我們遇到的實際問題。最重要的是，我們不是只修 bug，而是根據測試體驗改良操作設計，例如把不敏感的手勢換成更容易辨識的上滑下滑。

### Slide 15｜資料夾與模組分工

分工可以依資料夾切。這樣每個人負責的範圍明確，也符合評分規範中要求的團隊合作分工。

### Slide 16｜Demo 操作腳本

現場展示建議按照這個順序，先展示點餐核心功能，再展示模式切換和虛擬滑鼠。這樣觀眾比較容易理解系統從點餐到進階控制的完整性。

### Slide 17｜可能問題 1：為什麼不用 AI 分類模型？

如果老師問為什麼不用訓練模型，可以回答：目前手勢種類有限，規則式判斷已足夠，而且可解釋性高、延遲低。未來要擴充大量手勢時，才更適合導入模型分類。

### Slide 18｜可能問題 2：如何避免誤觸？

這題可以從四個機制回答：冷卻時間、穩定停留、兩段式確認、滑鼠死區。這些設計都是為了降低誤觸，讓展示更穩。

### Slide 19｜可能問題 3：系統限制與改善方向

這頁要誠實說明限制，同時提出合理改善方向。重點是讓老師看到我們知道系統還可以怎麼進步，而不是假裝沒有問題。

### Slide 20｜程式碼講解分區

如果報告時間足夠，可以用這頁進入程式碼講解。建議不要逐行講，而是依照模組分區，講每個區塊的責任、核心函式和為什麼這樣設計。

### Slide 21｜結論

結論要收斂到成果：我們完成了一個可以展示的手勢點餐系統，而且不只是辨識手勢，還包含完整的網頁互動、確認流程和測試驗證。

## 程式碼分區註解文字稿

### main.py 主流程

- run_flask()：把 Flask Server 放到背景執行緒，讓主執行緒可以保留給 OpenCV 攝影機迴圈。
- connect_socketio_client()：主程式用 Socket.IO Client 連回本機 Flask Server，把手勢事件送到前端。
- initialize_detector()：初始化 HandDetector，若 MediaPipe 不可用則提示使用者檢查 Python 與套件版本。
- get_palm_center()：用多個掌心附近 landmarks 平均，讓滑鼠控制比單一指尖更穩定。
- compute_cursor_speed()：加入 deadzone 與速度上限，避免手部微抖造成游標漂移。
- main()：讀取 webcam frame、偵測手、依目前模式執行 Focus 或 Mouse 行為。

### vision/gesture_logic.py 手勢邏輯

- can_trigger()：統一管理冷卻時間，避免同一手勢短時間重複觸發。
- detect_swipe()：用食指指尖 x/y 位移判斷 LEFT、RIGHT、PLUS、MINUS。
- detect_ok_gesture()：拇指與食指靠近，且其他三指伸直時觸發 CHECKOUT。
- detect_mode_switch()：要求張開手掌穩定停留，降低一般滑動時誤切模式。
- detect_mouse_click()：拇指姿勢成立時觸發滑鼠左鍵，並用 ready 狀態避免連點。

### vision/hand_detector.py 手部偵測

- HandDetector 優先使用 MediaPipe Tasks API，因為 landmarks 品質較穩。
- Tasks 初始化失敗時改用 MediaPipe Solutions，增加環境相容性。
- 若 MediaPipe 無法使用，可保留 OpenCV fallback 方便開發除錯。
- SimpleLandmarksContainer 統一輸出格式，讓 GestureLogic 不需知道目前是哪種偵測器。

### vision/webcam.py 攝影機

- 初始化時設定解析度與 FPS，提升手部偵測畫面品質。
- get_frame() 會鏡像畫面，讓使用者看到的方向與手勢方向一致。
- release() 負責釋放攝影機資源，避免下次啟動時被占用。

### control/focus_mode.py Focus 模式

- current_index 記錄目前選到第幾個餐點。
- RIGHT / LEFT 會用循環方式切換餐點，讓使用者不用擔心超出範圍。
- PLUS / MINUS 對目前餐點加減數量。
- CHECKOUT 不改變餐點索引，而是通知前端進入確認流程。

### control/virtual_mouse.py 虛擬滑鼠

- 使用 Windows user32 API 控制游標，符合目前展示環境。
- move_by() 用相對位移控制游標，是主系統 Mouse Mode 的核心。
- _initialize_from_system_cursor() 先讀取目前游標位置，避免切換模式時游標突然跳動。
- click_left() 模擬滑鼠左鍵按下與放開。

### flask_server/app.py Flask 後端

- home() 回傳主頁 index.html。
- handle_mode_change() 接收前端模式切換，並同步通知所有連線端。
- handle_gesture() 接收 main.py 傳來的手勢，只有 Focus Mode 會更新菜單。
- FocusMode(item_count=5) 表示後端只管理 5 個餐點，確認餐點由 OK 手勢獨立觸發。

### flask_server/static/script.js 前端互動

- getSelectableItems() 取得 5 個餐點卡片，確認餐點不混入餐點循環。
- increase() / decrease() 更新數量與總金額。
- handleCheckoutConfirm() 是兩段式 OK 的核心：明細未開時開明細，已開時送出訂單。
- socket.on('focus_update') 依 MOVE、INCREASE、DECREASE、CHECKOUT 更新 UI。

### flask_server/templates/index.html 與 style.css

- index.html 負責菜單結構、模式區、手勢教學、確認餐點與訂單明細彈窗。
- style.css 用卡片、右側教學、底部狀態列分區，讓展示時畫面清楚。
- 手勢教學使用 SVG 貼圖，讓使用者能直接看懂每個動作。

### tests/test_gesture_logic.py 測試

- 使用簡化 Landmark 模擬 MediaPipe 輸出，讓測試不依賴攝影機。
- 測試張開手掌、模式切換、左右滑、上下滑與 OK 手勢。
- 目前 6 個單元測試通過，可降低手勢邏輯修改後壞掉的風險。

## 可能問答總整理

### Q1：為什麼不用深度學習模型分類所有手勢？
A：目前手勢種類有限，使用 landmarks 幾何規則即可達成，延遲低、可解釋、容易調整。未來若要擴充更多手勢，才適合加入訓練模型。

### Q2：如何避免誤觸？
A：系統使用冷卻時間、模式切換停留判斷、滑鼠 deadzone，以及兩段式 OK 確認，避免手勢連續觸發或直接送出訂單。

### Q3：MediaPipe 如果在不同電腦跑不起來怎麼辦？
A：建議統一 Python 3.11 與 requirements.txt 版本；系統也設計了 Tasks、Solutions 與 OpenCV fallback，降低展示失敗風險。

### Q4：為什麼確認餐點不用握拳？
A：實測握拳敏感度較不穩，OK 手勢在視覺上也更符合確認語意，因此改成 OK 兩段式確認。

### Q5：這個系統的限制是什麼？
A：光線、背景、手部遮擋都會影響 landmarks；目前以單手與 Windows 展示為主，未來可加入校正、資料庫與跨平台支援。
