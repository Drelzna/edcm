import os
import sys
import time

import cv2
import win32con
import win32gui
from numpy import sum

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from edcm import windows
from edcm import screen
import colorlog

logger = colorlog.getLogger()

logger.info(sys.path)

hwnd = win32gui.GetForegroundWindow()
windows.get_hwnd_info(hwnd)

screen_size = screen.get_elite_size()
assert screen_size is not None
logger.info("screen_size['left'] = %s, screen_size['top'] = %s, screen_size['width'] = %s, screen_size['height'] = %s",
            screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height'])

viewer = cv2.namedWindow("Test Screen",cv2.WINDOW_NORMAL)


windows.set_elite_active_window()

while True:
    screen_size = screen.get_elite_size()
    windows.set_elite_active_window()
    img = screen.get_screen(screen_size)
    cv2.imshow("test_screen.py", img)
    test_hwnd = windows.get_hwnd("Test Screen")
    windows.set_active_window(test_hwnd)
    # Press "q" to quit
    if cv2.waitKey(25) & 0xFF == ord("q"):
        cv2.destroyAllWindows()
        break

filter_orange = screen.filter_orange(img, testing=True)
filter_blue = screen.filter_blue(img, testing=True)
filter_bright_image = screen.filter_bright(img, testing=True)

filter_sun = screen.filter_sun(img, testing=True)
logger.info("filter_sun white == %.2f" % sum(filter_sun == 255))
logger.info("filter_sun black == %.2f" % sum(filter_sun != 255))

hsv_image = screen.hsv_slider(bandw=True)

win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
try:
    win32gui.SetForegroundWindow(hwnd)
except Exception as e:
    logger.fatal(e)
