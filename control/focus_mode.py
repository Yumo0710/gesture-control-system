import time


class FocusMode:

    def __init__(self):

        # 目前焦點位置
        self.current_index = 0

        # 商品數量
        self.max_index = 4

        # 上次觸發時間
        self.last_trigger_time = 0

        # 冷卻時間
        self.cooldown = 0.3


    # 更新 Focus
    def update(self, gesture):

        current_time = time.time()


        # 冷卻中
        if current_time - self.last_trigger_time < self.cooldown:

            return None


        # 更新時間
        self.last_trigger_time = current_time


        # RIGHT
        if gesture == "RIGHT":

            self.current_index += 1

            if self.current_index > self.max_index:

                self.current_index = 0

            return {

                "type": "MOVE",

                "index": self.current_index
            }


        # LEFT
        elif gesture == "LEFT":

            self.current_index -= 1

            if self.current_index < 0:

                self.current_index = self.max_index

            return {

                "type": "MOVE",

                "index": self.current_index
            }


        # PLUS
        elif gesture == "PLUS":

            return {

                "type": "INCREASE",

                "index": self.current_index
            }


        # MINUS
        elif gesture == "MINUS":

            return {

                "type": "DECREASE",

                "index": self.current_index
            }


        # SELECT
        elif gesture == "SELECT":

            return {

                "type": "SELECT",

                "index": self.current_index
            }


        # BACK
        elif gesture == "BACK":

            return {

                "type": "BACK",

                "index": self.current_index
            }


        return None


    # 取得目前 Focus
    def get_index(self):

        return self.current_index
