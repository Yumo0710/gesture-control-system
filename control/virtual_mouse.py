import ctypes
import ctypes.wintypes


class VirtualMouse:
    def __init__(self, smoothing=0.25):
        # 透過 Windows user32 API 控制游標，專題目前以 Windows 展示為主。
        self.user32 = ctypes.windll.user32
        self.screen_width = self.user32.GetSystemMetrics(0)
        self.screen_height = self.user32.GetSystemMetrics(1)
        self.smoothing = smoothing
        self.current_x = None
        self.current_y = None

    def _clamp_to_screen(self):
        self.current_x = max(0, min(self.screen_width - 1, self.current_x))
        self.current_y = max(0, min(self.screen_height - 1, self.current_y))

    def _initialize_from_system_cursor(self):
        # 切到 Mouse Mode 時先讀取目前游標位置，避免游標突然跳到畫面角落。
        point = ctypes.wintypes.POINT()
        try:
            self.user32.GetCursorPos(ctypes.byref(point))
            self.current_x, self.current_y = point.x, point.y
        except Exception:
            self.current_x = int(self.screen_width / 2)
            self.current_y = int(self.screen_height / 2)

    def move(self, normalized_x, normalized_y):
        # 使用 0~1 的正規化座標控制絕對位置，主要給獨立測試腳本使用。
        normalized_x = max(0.0, min(1.0, normalized_x))
        normalized_y = max(0.0, min(1.0, normalized_y))

        target_x = int(normalized_x * self.screen_width)
        target_y = int(normalized_y * self.screen_height)

        if self.current_x is None or self.current_y is None:
            self.current_x = target_x
            self.current_y = target_y
        else:
            self.current_x += int((target_x - self.current_x) * self.smoothing)
            self.current_y += int((target_y - self.current_y) * self.smoothing)

        self._clamp_to_screen()
        self.user32.SetCursorPos(self.current_x, self.current_y)
        return self.current_x, self.current_y

    def move_by(self, dx, dy):
        # 使用相對位移控制游標，主系統的 Mouse Mode 會走這個方法。
        if self.current_x is None or self.current_y is None:
            self._initialize_from_system_cursor()

        self.current_x += int(dx)
        self.current_y += int(dy)
        self._clamp_to_screen()

        self.user32.SetCursorPos(self.current_x, self.current_y)
        return self.current_x, self.current_y

    def click_left(self):
        # 模擬滑鼠左鍵按下與放開。
        mouseeventf_leftdown = 0x0002
        mouseeventf_leftup = 0x0004
        self.user32.mouse_event(mouseeventf_leftdown, 0, 0, 0, 0)
        self.user32.mouse_event(mouseeventf_leftup, 0, 0, 0, 0)
