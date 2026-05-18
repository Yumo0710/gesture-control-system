# Models

此資料夾用來放置手勢辨識的預訓練模型。

目前主程式預設讀取：

```text
models/gesture_recognizer.task
```

請放入 MediaPipe Gesture Recognizer 的 `.task` 模型檔。模型存在時，`main.py` 會優先使用模型直接分類手勢；模型不存在時，會自動退回原本的 landmarks 規則，避免專案無法啟動。
