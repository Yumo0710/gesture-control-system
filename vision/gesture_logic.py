import math
import time


class GestureLogic:
    def __init__(self):
        self.previous_x = None
        self.previous_y = None

        # Focus Mode 使用食指指尖做四方向滑動：左右切換、上滑增加、下滑減少。
        self.swipe_threshold = 0.08

        # 共用觸發冷卻，避免同一個手勢在短時間內連續送出多次。
        self.cooldown = 0.5
        self.last_trigger_time = 0

        # Mouse Mode 點擊狀態，避免拇指維持同姿勢時連點。
        self.thumb_click_ready = True

        # OK 手勢狀態，讓確認餐點只在手勢剛成立時觸發一次。
        self.ok_gesture_ready = True

        # 模式切換使用穩定張開手掌停留，降低一般滑動時誤切模式。
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

    def _distance(self, first, second):
        return math.hypot(first.x - second.x, first.y - second.y)

    def _palm_center(self, hand_landmarks):
        # 取手腕與掌根附近關節平均值，作為判斷手掌是否穩定的中心點。
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

    def _finger_extended(self, hand_landmarks, tip_index, joint_index, threshold=0.06):
        tip_y = hand_landmarks.landmark[tip_index].y
        joint_y = hand_landmarks.landmark[joint_index].y
        return (joint_y - tip_y) > threshold

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
            if self._finger_extended(hand_landmarks, tip, joint):
                extended_count += 1

        return extended_count >= 4

    def detect_ok_gesture(self, hand_landmarks):
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]

        # OK 手勢以拇指與食指指尖靠近為主，再要求其餘三指伸直，避免和普通點擊混淆。
        thumb_index_close = self._distance(thumb_tip, index_tip) < 0.055
        other_fingers_extended = all(
            self._finger_extended(hand_landmarks, tip, joint, threshold=0.045)
            for tip, joint in [(12, 10), (16, 14), (20, 18)]
        )
        is_ok = thumb_index_close and other_fingers_extended

        if is_ok:
            if self.ok_gesture_ready and self.can_trigger():
                self.ok_gesture_ready = False
                self.previous_x = None
                self.previous_y = None
                return True
            return False

        self.ok_gesture_ready = True
        return False

    def detect_mode_switch(self, hand_landmarks):
        current_time = time.time()

        if current_time < self.mode_switch_cooldown_until:
            return False

        if not self.is_open_palm(hand_landmarks):
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

            # 手掌移動太多代表不是停留，重新計算模式切換時間。
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
            self.previous_y = None
            return True

        return False

    def detect_mouse_click(self, hand_landmarks):
        thumb_tip = hand_landmarks.landmark[4]
        thumb_ip = hand_landmarks.landmark[3]
        thumb_mcp = hand_landmarks.landmark[2]

        if thumb_tip.y < thumb_ip.y < thumb_mcp.y:
            if self.thumb_click_ready and self.can_trigger():
                self.thumb_click_ready = False
                return True
            return False

        self.thumb_click_ready = True
        return False

    def is_fist(self, hand_landmarks):
        # 保留握拳判斷給未來擴充與測試使用，目前不再用於餐點確認。
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
        index_finger = hand_landmarks.landmark[8]
        current_x = index_finger.x
        current_y = index_finger.y
        gesture = None

        if self.previous_x is not None and self.previous_y is not None:
            diff_x = current_x - self.previous_x
            diff_y = current_y - self.previous_y

            # 取位移量較大的方向，避免斜向動作同時觸發兩種操作。
            if abs(diff_x) >= abs(diff_y):
                if diff_x > self.swipe_threshold and self.can_trigger():
                    gesture = "RIGHT"
                elif diff_x < -self.swipe_threshold and self.can_trigger():
                    gesture = "LEFT"
            else:
                # 畫面 y 越小代表手往上，因此 diff_y < 0 是上滑。
                if diff_y < -self.swipe_threshold and self.can_trigger():
                    gesture = "PLUS"
                elif diff_y > self.swipe_threshold and self.can_trigger():
                    gesture = "MINUS"

        self.previous_x = current_x
        self.previous_y = current_y
        return gesture
