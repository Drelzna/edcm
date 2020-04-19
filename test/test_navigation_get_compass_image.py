import logging
import colorlog
import os
import sys
import win32con
import win32gui
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from edcm import navigation, windows, screen, galaxy_map


logging.basicConfig(filename='edcm.log', level=logging.DEBUG)
logger = colorlog.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(
    colorlog.ColoredFormatter('%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s',
                              log_colors={
                                  'DEBUG': 'fg_bold_cyan',
                                  'INFO': 'fg_bold_green',
                                  'WARNING': 'bg_bold_yellow,fg_bold_blue',
                                  'ERROR': 'bg_bold_red,fg_bold_white',
                                  'CRITICAL': 'bg_bold_red,fg_bold_yellow',
                              }, secondary_log_colors={}

                              ))
logger.addHandler(handler)

hwnd = win32gui.GetForegroundWindow()
windows.get_hwnd_info(hwnd)

screen_size = screen.get_elite_size()
assert screen_size is not None
logger.info("screen_size['left'] = %s, screen_size['top'] = %s, screen_size['width'] = %s, screen_size['height'] = %s",
            screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height'])

windows.set_elite_active_window()

# galaxy_map.set_destination("COL 285 SECTOR HU-K B23-7")
# galaxy_map.open_galaxy_map()
# galaxy_map.close_galaxy_map()

compass_image = navigation.get_compass_image(testing=True)

if hwnd:
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
        win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        logger.fatal(e)
