from win32gui import GetWindowRect, FindWindow, GetCursorInfo
from ctypes import windll

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_CLICK = MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_LEFTUP

class Clicker():
    def __init__(self, windowTitle: str):
        self.win_x, self.win_y, win_x2, win_y2 = GetWindowRect(FindWindow(None, windowTitle))
        self.win_w = win_x2 - self.win_x
        self.win_h = win_y2 - self.win_y

    def move(self, x: int, y: int):
        windll.user32.SetCursorPos(x - self.win_x, y - self.win_y)

    def move_frac(self, x: float, y: float):
        windll.user32.SetCursorPos(
            round(self.win_w * x + self.win_x),
            round(self.win_h * y + self.win_y)
        )
        
    def click():
        windll.user32.mouse_event(MOUSEEVENTF_CLICK, 0, 0, 0, 0)

    def mouse_down():
        windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

    def mouse_up():
        windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def get_pos(self):
        _, _, (x, y) = GetCursorInfo()
        return x - self.win_x, y - self.win_y

    def get_pos_frac(self):
        x, y = self.get_pos()
        return x / self.win_w, y / self.win_h
