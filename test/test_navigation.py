import os
import sys
import colorlog
import win32con
import win32gui


logger = colorlog.getLogger()

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from edcm import navigation, windows, screen, galaxy_map

hwnd = win32gui.GetForegroundWindow()
windows.get_hwnd_info(hwnd)

screen_size = screen.get_elite_size()
assert screen_size is not None
logger.info("screen_size['left'] = %s, screen_size['top'] = %s, screen_size['width'] = %s, screen_size['height'] = %s",
            screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height'])

windows.set_elite_active_window()

galaxy_map.set_destination("SIRIUS")

navigation.autopilot()

win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
try:
    win32gui.SetForegroundWindow(hwnd)
except Exception as e:
    logger.fatal(e)
