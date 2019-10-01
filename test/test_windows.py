import os
import sys
from time import sleep
import win32gui
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from edcm import windows

print(sys.path)

# hwnd = windows.get_hwnd("notepad","Untitled - Notepad")
# windows.print_hwnd_info(hwnd)

hwnd = windows.get_my_hwnd()

elite_hwnd = windows.get_elite_hwnd()
windows.print_hwnd_info(elite_hwnd)

print("Elite Dangerous is active window...")
win32gui.SetForegroundWindow(elite_hwnd)

sleep(10)

print("Return to original window")
win32gui.SetForegroundWindow(hwnd)

