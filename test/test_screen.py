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

windows.set_elite_active_window()

img = screen.get_screen()
assert img is not None

filter_orange = screen.filter_orange(None, testing=True)
filter_blue = screen.filter_blue(None, testing=True)
filter_bright_image = screen.filter_bright(None, testing=True)

filter_sun = screen.filter_sun(None, testing=True)
logger.info("filter_sun white == %.2f" % sum(filter_sun == 255))
logger.info("filter_sun black == %.2f" % sum(filter_sun != 255))

interval = 3
start_time = time.time()
fps = 0
img = screen.get_screen(screen_size)
cv2.imshow("test_screen.py", img)
while True:
    img = screen.get_screen(screen_size)
    fps += 1
    elapsed = time.time() - start_time
    if elapsed >= interval:
        print("FPS: ", fps / elapsed)
        # set fps again to zero
        fps = 0
        # set start time to current time again
        start_time = time.time()
    # Press "q" to quit
    if cv2.waitKey(25) & 0xFF == ord("q"):
        cv2.destroyAllWindows()
        break

hsv_image = screen.hsv_slider(bandw=True)

win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
try:
    win32gui.SetForegroundWindow(hwnd)
except Exception as e:
    logger.fatal(e)
