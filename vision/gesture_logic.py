import math
import time


class GestureLogic:
    def __init__(self):
        self.previous_x = None

        # 左右揮動的距離門檻，避免手指小幅晃動就切換餐點。
        self.swipe_threshold = 0.08

        # 一般手勢冷卻時間，避免同一個動作連續觸發太多次。
        self.cooldown = 0.5
        self.last_trigger_time = 0

        # Focus Mode 的數量調整狀態：握拳後才接受拇指增減。
        self.value_mode = False
        self.thumb_ready = False

        # Mouse Mode 點擊狀態，避免拇指維持同姿勢時連點。
        self.thumb_click_ready = True

        # 模式切換使用張開手掌停留，獨立冷卻避免切換後立刻又切回去。
        self.mode_switch_start_time = None
        self.mode_switch_last_center = None
        self.mode_switch_cooldown_until = 0
        self.mode_switch_hold_seconds = 1.0
        self.mode_switch_motion_threshold = 0.05

    def can_trigger(self):
        current_time = time.time()
        if current_time - self.last_trigger_time < self.cooldown:
            return False

        self.last_trigger_time = current_time
        return True

    def _palm_center(self, hand_landmarks):
        # 用手腕與掌根附近的點平均，取得比單一指尖更穩定的手掌中心。
        palm_indices = [0, 1, 2, 5, 9, 13, 17]
        xs = []
        ys = []

        for index in palm_indices:
            if index < len(hand_landmarks.landmark):
                xs.append(hand_landmarks.landmark[index].x)
                ys.append(hand_landmarks.landmark[index].y)

        if not xs or not ys:
            return None

        return sum(xs) / len(xs), sum(ys) / len(ys)

    def is_open_palm(self, hand_landmarks):
        # 判斷四指是否伸直；不強判拇指，降低左右手方向造成的誤判。
        fingers = [
            (8, 6),    # 食指
            (12, 10),  # 中指
            (16, 14),  # 無名指
            (20, 18),  # 小指
        ]

        extended_count = 0
        for tip, joint in fingers:
            tip_y = hand_landmarks.landmark[tip].y
            joint_y = hand_landmarks.landmark[joint].y

            if (joint_y - tip_y) > 0.06:
                extended_count += 1

        return extended_count >= 4

    def detect_mode_switch(self, hand_landmarks):
        current_time = time.time()

        if current_time < self.mode_switch_cooldown_until:
            return False

        if self.value_mode or not self.is_open_palm(hand_landmarks):
            self.mode_switch_start_time = None
            self.mode_switch_last_center = None
            return False

        center = self._palm_center(hand_landmarks)
        if center is None:
            return False

        if self.mode_switch_last_center is not None:
            dx = center[0] - self.mode_switch_last_center[0]
            dy = center[1] - self.mode_switch_last_center[1]
            movement = math.hypot(dx, dy)

            # 手掌移動太多就重新計時，要求「張開手掌停住」才切換模式。
            if movement > self.mode_switch_motion_threshold:
                self.mode_switch_start_time = current_time

        if self.mode_switch_start_time is None:
            self.mode_switch_start_time = current_time

        self.mode_switch_last_center = center

        if current_time - self.mode_switch_start_time >= self.mode_switch_hold_seconds:
            self.mode_switch_start_time = None
            self.mode_switch_last_center = None
            self.mode_switch_cooldown_until = current_time + 1.5
            self.previous_x = None
            print("MODE SWITCH")
            return True

        return False

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

    def calculate_angle(self, p1, p2):
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        return math.degrees(math.atan2(dy, dx))

    def is_fist(self, hand_landmarks):
        fingers = [
            (8, 6),    # 食指
            (12, 10),  # 中指
            (16, 14),  # 無名指
            (20, 18),  # 小指
        ]

        folded_count = 0
        for tip, joint in fingers:
            tip_y = hand_landmarks.landmark[tip].y
            joint_y = hand_landmarks.landmark[joint].y

            if (tip_y - joint_y) > 0.08:
                folded_count += 1

        return folded_count >= 4

    def detect_swipe(self, hand_landmarks):
        # 進入數量調整狀態後暫停左右揮動，避免調整時又切換餐點。
        if self.value_mode:
            return None

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

            if diff_x > self.swipe_threshold:
                if self.can_trigger():
                    gesture = "RIGHT"
            elif diff_x < -self.swipe_threshold:
                if self.can_trigger():
                    gesture = "LEFT"

        self.previous_x = current_x
        return gesture

    def detect_thumb(self, hand_landmarks):
        if not self.value_mode:
            return None

        thumb_tip = hand_landmarks.landmark[4]
        thumb_joint = hand_landmarks.landmark[2]
        angle = self.calculate_angle(thumb_joint, thumb_tip)

        if not self.thumb_ready:
            # 拇指先回到水平附近才開始接受上下指令，降低剛握拳時的誤判。
            if -20 < angle < 20:
                self.thumb_ready = True
                print("THUMB READY")
            return None

        if angle < -40:
            if self.can_trigger():
                self.value_mode = False
                print("PLUS")
                return "PLUS"

        if angle > 40:
            if self.can_trigger():
                self.value_mode = False
                print("MINUS")
                return "MINUS"

        return None
