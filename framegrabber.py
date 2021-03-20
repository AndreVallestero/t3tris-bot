import win32gui, win32ui
from win32con import SRCCOPY
from numpy import fromstring

'''
Optimized to be 6 times faster using the following techniques
- Reuse bitmaps, handles, and device contexts
- Use the application framebuffer instead of the compositor frame buffer(entire desktop)

This is not the fastest method. That would be to directly copy the data from the GPU back buffer
- https://web.archive.org/web/20121205062922/http://www.ring3circus.com/blog/2007/11/22/case-study-fraps/
'''

class FrameGrabber():
    def __init__(self, x: float, y: float, w: float, h: float, windowTitle: str = ""):
        self.hwnd = win32gui.FindWindow(None, windowTitle) if windowTitle else win32gui.GetDesktopWindow()
        win_x1, win_y1, win_x2, win_y2 = win32gui.GetWindowRect(self.hwnd)
        win_w = win_x2 - win_x1
        win_h = win_y2 - win_y1
        self.pos = (
            round(x * win_w if 0 < x < 1 else x),
            round(y * win_h if 0 < y < 1 else y)
        )
        self.w = round(w * win_w if 0 < w < 1 else w)
        self.h = round(h * win_h if 0 < h < 1 else h)
        print(self.w, self.h, win_w, win_h)
        
        self.hwnddc = win32gui.GetWindowDC(self.hwnd)
        self.hdcSrc = win32ui.CreateDCFromHandle(self.hwnddc)
        self.hdcDest = self.hdcSrc.CreateCompatibleDC()

        self.bmp = win32ui.CreateBitmap()
        self.bmp.CreateCompatibleBitmap(self.hdcSrc, self.w, self.h)
        self.hdcDest.SelectObject(self.bmp)

    def grab(self):
        self.hdcDest.BitBlt((0, 0), (self.w, self.h), self.hdcSrc, self.pos, SRCCOPY)
        img = fromstring(self.bmp.GetBitmapBits(True), dtype='uint8')
        img.shape = (self.h ,self.w, 4)

        # To convert to RGB, use cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        # This is often unnecessary if simple image filtering is being done
        return img

    def __del__(self):
        self.hdcSrc.DeleteDC()
        self.hdcDest.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, self.hwnddc)
        win32gui.DeleteObject(self.bmp.GetHandle())
        
