import os
import sys
import win32gui
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from edcm import menu
from edcm import windows

print(sys.path)

# window focus "Elite - Dangerous (CLIENT)"
elite_hwnd = windows.get_elite_hwnd()
windows.print_hwnd_info(elite_hwnd)
win32gui.SetForegroundWindow(elite_hwnd)

menu.start_solo()
win32gui.SetForegroundWindow(elite_hwnd)
menu.exit_to_main_menu()

menu.start_open()
win32gui.SetForegroundWindow(elite_hwnd)
menu.exit_to_main_menu()
