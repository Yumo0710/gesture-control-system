import ctypes


class VirtualMouse:
    def __init__(self, smoothing=0.25):
        self.user32 = ctypes.windll.user32
        self.screen_width = self.user32.GetSystemMetrics(0)
        self.screen_height = self.user32.GetSystemMetrics(1)
        self.smoothing = smoothing
        self.current_x = None
        self.current_y = None

    def move(self, normalized_x, normalized_y):
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

        self.user32.SetCursorPos(self.current_x, self.current_y)
        return self.current_x, self.current_y
