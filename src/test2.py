import ctypes
import time

GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState

VK_LEFT = 0x25
VK_DOWN = 0x28

while True:
    left = GetAsyncKeyState(VK_LEFT)
    down = GetAsyncKeyState(VK_DOWN)
    if left & 0x8000 and down & 0x8000:
        print("Left + Down")
    time.sleep(0.05)