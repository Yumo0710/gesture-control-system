import time


class FocusMode:
    def __init__(self, item_count=5, cooldown=0.3):
        # 目前選取的菜單索引，前端菜單目前共有 5 個項目。
        self.current_index = 0
        self.max_index = max(0, item_count - 1)

        # 避免同一個手勢在短時間內重複觸發。
        self.last_trigger_time = 0
        self.cooldown = cooldown

    def _cooling_down(self):
        current_time = time.time()
        if current_time - self.last_trigger_time < self.cooldown:
            return True

        self.last_trigger_time = current_time
        return False

    def update(self, gesture):
        # Focus Mode 只處理菜單移動與數量調整指令。
        if self._cooling_down():
            return None

        if gesture == "RIGHT":
            self.current_index = (self.current_index + 1) % (self.max_index + 1)
            return {"type": "MOVE", "index": self.current_index}

        if gesture == "LEFT":
            self.current_index = (self.current_index - 1) % (self.max_index + 1)
            return {"type": "MOVE", "index": self.current_index}

        if gesture == "PLUS":
            return {"type": "INCREASE", "index": self.current_index}

        if gesture == "MINUS":
            return {"type": "DECREASE", "index": self.current_index}

        if gesture == "SELECT":
            return {"type": "SELECT", "index": self.current_index}

        if gesture == "CHECKOUT":
            return {"type": "CHECKOUT", "index": self.current_index}

        return None

    def get_index(self):
        # 提供測試或除錯時讀取目前選取位置。
        return self.current_index
