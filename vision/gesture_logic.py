import time
import math


class GestureLogic:

    def __init__(self):

        self.previous_x = None

        # 左右滑動閾值
        self.swipe_threshold = 0.08

        # 冷卻時間
        self.cooldown = 0.5

        self.last_trigger_time = 0

        # 是否進入加減模式
        self.value_mode = False

        # 大拇指是否已回到中立
        self.thumb_ready = False

        # 滑鼠點擊準備狀態
        self.thumb_click_ready = True


    # =========================
    # 冷卻時間判定
    # =========================
    def can_trigger(self):

        current_time = time.time()

        if current_time - self.last_trigger_time < self.cooldown:

            return False

        self.last_trigger_time = current_time

        return True


    def detect_mouse_click(self, hand_landmarks):
        thumb_tip = hand_landmarks.landmark[4]
        thumb_ip = hand_landmarks.landmark[3]
        thumb_mcp = hand_landmarks.landmark[2]

        if thumb_tip.y < thumb_ip.y < thumb_mcp.y:
            if self.thumb_click_ready and self.can_trigger():
                self.thumb_click_ready = False
                print("LEFT CLICK")
                return True
            return False

        self.thumb_click_ready = True
        return False


    # =========================
    # 計算角度
    # =========================
    def calculate_angle(self, p1, p2):

        dx = p2.x - p1.x

        dy = p2.y - p1.y

        angle = math.degrees(

            math.atan2(dy, dx)

        )

        return angle


    # =========================
    # 握拳判定
    # =========================
    def is_fist(self, hand_landmarks):

        fingers = [

            (8, 6),    # 食指
            (12, 10),  # 中指
            (16, 14),  # 無名指
            (20, 18)   # 小指
        ]

        folded_count = 0

        for tip, joint in fingers:

            tip_y = hand_landmarks.landmark[tip].y

            joint_y = hand_landmarks.landmark[joint].y

            # 必須彎曲超過一定距離
            if (tip_y - joint_y) > 0.08:

                folded_count += 1

        # 至少4指真的彎曲
        return folded_count >= 4


    # =========================
    # 左右滑動
    # =========================
    def detect_swipe(self, hand_landmarks):

        # Value Mode 中
        # 不允許左右滑動
        if self.value_mode:

            return None


        # 握拳進入 Value Mode
        if self.is_fist(hand_landmarks):

            if self.can_trigger():

                self.value_mode = True

                self.thumb_ready = False

                print("ENTER VALUE MODE")

            return None


        index_finger = hand_landmarks.landmark[8]

        current_x = index_finger.x

        gesture = None


        if self.previous_x is not None:

            diff_x = current_x - self.previous_x


            # 往右
            if diff_x > self.swipe_threshold:

                if self.can_trigger():

                    gesture = "RIGHT"


            # 往左
            elif diff_x < -self.swipe_threshold:

                if self.can_trigger():

                    gesture = "LEFT"


        self.previous_x = current_x

        return gesture


    # =========================
    # 大拇指偵測
    # =========================
    def detect_thumb(self, hand_landmarks):

        # 未進入 Value Mode
        if not self.value_mode:

            return None


        thumb_tip = hand_landmarks.landmark[4]

        thumb_joint = hand_landmarks.landmark[2]


        # 計算大拇指角度
        angle = self.calculate_angle(

            thumb_joint,

            thumb_tip

        )



        # =========================
        # 等待回中立
        # =========================
        if not self.thumb_ready:

            # 接近水平
            if -20 < angle < 20:

                self.thumb_ready = True

                print("THUMB READY")

            return None


        # =========================
        # 👍 PLUS
        # =========================
        if angle < -40:

            if self.can_trigger():

                self.value_mode = False

                print("PLUS")

                return "PLUS"


        # =========================
        # 👎 MINUS
        # =========================
        elif angle > 40:

            if self.can_trigger():

                self.value_mode = False

                print("MINUS")

                return "MINUS"


        return None