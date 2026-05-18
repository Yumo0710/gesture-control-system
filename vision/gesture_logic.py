import math
import time


class GestureLogic:

    def __init__(self):

        # 冷卻時間避免同一個姿勢在短時間內重複觸發。
        self.cooldown = 0.6

        self.last_trigger_time = 0

        self.pending_gesture = None

        self.pending_count = 0

        # 同一個姿勢需要連續出現數幀，降低手指抖動或短暫誤判。
        self.stable_frames = 3


    def can_trigger(self):

        current_time = time.time()

        if current_time - self.last_trigger_time < self.cooldown:

            return False

        self.last_trigger_time = current_time

        return True


    def detect_gesture(self, hand_landmarks):

        raw_gesture = self._detect_raw_gesture(hand_landmarks)

        if raw_gesture is None:

            self._reset_pending()

            return None

        return self._get_stable_gesture(raw_gesture)


    def _detect_raw_gesture(self, hand_landmarks):

        points = hand_landmarks.landmark

        # OK 手勢代表完成購物，優先判斷可避免被食指彎曲狀態誤認成握拳。
        if self._is_ok(points):

            return "SELECT"

        # 手掌全開代表返回上一頁，和握拳減少做出明顯區隔。
        if self._is_open_palm(points):

            return "BACK"

        # 握拳代表減少商品，避開劍指向下容易被手掌遮擋的問題。
        if self._is_fist(points):

            return "MINUS"

        # 食指單獨伸直且其他手指握拳，用食指方向控制頁面左右移動。
        index_direction = self._finger_direction(points, 5, 8)

        if (
            index_direction in ("LEFT", "RIGHT")
            and self._is_index_only(points)
        ):

            return index_direction

        # 食指與中指同時伸直形成劍指，僅使用向上姿勢控制目前商品增加。
        sword_direction = self._sword_direction(points)

        if sword_direction:

            return sword_direction

        return None


    def _get_stable_gesture(self, gesture):

        if gesture == self.pending_gesture:

            self.pending_count += 1

        else:

            self.pending_gesture = gesture

            self.pending_count = 1

        if self.pending_count < self.stable_frames:

            return None

        if not self.can_trigger():

            return None

        self._reset_pending()

        return gesture


    def _reset_pending(self):

        self.pending_gesture = None

        self.pending_count = 0


    def _distance(self, p1, p2):

        return math.hypot(p1.x - p2.x, p1.y - p2.y)


    def _finger_direction(self, points, mcp_index, tip_index):

        mcp = points[mcp_index]

        tip = points[tip_index]

        dx = tip.x - mcp.x

        dy = tip.y - mcp.y

        # 只有位移足夠大才視為伸直方向，避免半彎曲手指造成誤判。
        if math.hypot(dx, dy) < 0.12:

            return None

        if abs(dx) > abs(dy) * 1.35:

            if dx > 0:

                return "RIGHT"

            return "LEFT"

        if abs(dy) > abs(dx) * 1.2:

            if dy < 0:

                return "UP"

            return "DOWN"

        return None


    def _is_folded(self, points, tip_index, pip_index, mcp_index):

        tip = points[tip_index]

        pip = points[pip_index]

        mcp = points[mcp_index]

        tip_to_mcp = self._distance(tip, mcp)

        pip_to_mcp = self._distance(pip, mcp)

        # 彎曲手指通常指尖會靠近掌指關節，並且不會明顯超過 PIP 到 MCP 的距離。
        return tip.y > pip.y - 0.02 and tip_to_mcp < pip_to_mcp * 1.45


    def _is_thumb_folded(self, points):

        thumb_tip = points[4]

        index_mcp = points[5]

        wrist = points[0]

        # 拇指靠近食指根部或手腕附近時，視為收進握拳狀態。
        return (
            self._distance(thumb_tip, index_mcp) < 0.13
            or self._distance(thumb_tip, wrist) < 0.22
        )


    def _is_index_only(self, points):

        return (
            self._finger_direction(points, 5, 8) in ("LEFT", "RIGHT")
            and self._is_folded(points, 12, 10, 9)
            and self._is_folded(points, 16, 14, 13)
            and self._is_folded(points, 20, 18, 17)
        )


    def _sword_direction(self, points):

        index_direction = self._finger_direction(points, 5, 8)

        middle_direction = self._finger_direction(points, 9, 12)

        if index_direction != middle_direction:

            return None

        if index_direction != "UP":

            return None

        ring_folded = self._is_folded(points, 16, 14, 13)

        pinky_folded = self._is_folded(points, 20, 18, 17)

        if not (ring_folded and pinky_folded):

            return None

        # 劍指只保留向上增加，避免向下姿勢因遮擋而偵測不穩。
        return "PLUS"


    def _is_ok(self, points):

        thumb_tip = points[4]

        index_tip = points[8]

        middle_direction = self._finger_direction(points, 9, 12)

        ring_direction = self._finger_direction(points, 13, 16)

        pinky_direction = self._finger_direction(points, 17, 20)

        # OK 手勢以拇指和食指指尖接近為核心，其他三指需明顯伸出以區隔握拳。
        return (
            self._distance(thumb_tip, index_tip) < 0.07
            and middle_direction == "UP"
            and ring_direction == "UP"
            and pinky_direction == "UP"
        )


    def _is_fist(self, points):

        return (
            self._is_folded(points, 8, 6, 5)
            and self._is_folded(points, 12, 10, 9)
            and self._is_folded(points, 16, 14, 13)
            and self._is_folded(points, 20, 18, 17)
            and self._is_thumb_folded(points)
        )


    def _is_open_palm(self, points):

        index_direction = self._finger_direction(points, 5, 8)

        middle_direction = self._finger_direction(points, 9, 12)

        ring_direction = self._finger_direction(points, 13, 16)

        pinky_direction = self._finger_direction(points, 17, 20)

        thumb_tip = points[4]

        index_mcp = points[5]

        # 手掌全開要求四指都向上伸直，且拇指離開掌心，避免被 OK 或握拳誤觸發。
        return (
            index_direction == "UP"
            and middle_direction == "UP"
            and ring_direction == "UP"
            and pinky_direction == "UP"
            and self._distance(thumb_tip, index_mcp) > 0.12
        )
