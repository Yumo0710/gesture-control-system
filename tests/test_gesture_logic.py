import time
import unittest

from vision.gesture_logic import GestureLogic


class Landmark:
    def __init__(self, x=0.5, y=0.5):
        self.x = x
        self.y = y


class HandLandmarks:
    def __init__(self, points):
        self.landmark = points


def make_hand():
    # 建立一組簡化的 21 點 landmarks，供手勢邏輯單元測試使用。
    points = [Landmark() for _ in range(21)]
    return HandLandmarks(points)


def make_open_palm():
    hand = make_hand()
    for tip, joint in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        hand.landmark[tip].y = 0.25
        hand.landmark[joint].y = 0.45
    return hand


def make_fist():
    hand = make_hand()
    for tip, joint in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        hand.landmark[tip].y = 0.55
        hand.landmark[joint].y = 0.40
    return hand


def make_ok_gesture():
    hand = make_hand()
    # OK 手勢：拇指與食指靠近，其餘三指伸直。
    hand.landmark[4].x = 0.50
    hand.landmark[4].y = 0.50
    hand.landmark[8].x = 0.53
    hand.landmark[8].y = 0.51

    for tip, joint in [(12, 10), (16, 14), (20, 18)]:
        hand.landmark[tip].y = 0.25
        hand.landmark[joint].y = 0.42

    return hand


class GestureLogicTests(unittest.TestCase):
    def test_open_palm_detection(self):
        logic = GestureLogic()
        self.assertTrue(logic.is_open_palm(make_open_palm()))
        self.assertFalse(logic.is_open_palm(make_fist()))

    def test_mode_switch_requires_hold_time(self):
        logic = GestureLogic()
        hand = make_open_palm()

        self.assertFalse(logic.detect_mode_switch(hand))
        logic.mode_switch_start_time = time.time() - logic.mode_switch_hold_seconds
        self.assertTrue(logic.detect_mode_switch(hand))

    def test_focus_swipe_right(self):
        logic = GestureLogic()
        hand = make_hand()

        hand.landmark[8].x = 0.3
        self.assertIsNone(logic.detect_swipe(hand))

        logic.last_trigger_time = 0
        hand.landmark[8].x = 0.45
        self.assertEqual(logic.detect_swipe(hand), "RIGHT")

    def test_focus_swipe_up_is_plus(self):
        logic = GestureLogic()
        hand = make_hand()

        hand.landmark[8].y = 0.55
        self.assertIsNone(logic.detect_swipe(hand))

        logic.last_trigger_time = 0
        hand.landmark[8].y = 0.40
        self.assertEqual(logic.detect_swipe(hand), "PLUS")

    def test_focus_swipe_down_is_minus(self):
        logic = GestureLogic()
        hand = make_hand()

        hand.landmark[8].y = 0.40
        self.assertIsNone(logic.detect_swipe(hand))

        logic.last_trigger_time = 0
        hand.landmark[8].y = 0.55
        self.assertEqual(logic.detect_swipe(hand), "MINUS")

    def test_ok_gesture_confirms_checkout(self):
        logic = GestureLogic()

        self.assertTrue(logic.detect_ok_gesture(make_ok_gesture()))
        self.assertFalse(logic.detect_ok_gesture(make_ok_gesture()))

        logic.last_trigger_time = 0
        self.assertFalse(logic.detect_ok_gesture(make_open_palm()))


if __name__ == "__main__":
    unittest.main()
