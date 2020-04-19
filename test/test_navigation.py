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

# galaxy_map.set_destination("NANOMAM")

# navigation.auto_launch()

navigation.navigation_align()

compass_image = navigation.get_compass_image(testing=True)

# sun_percent = navigation.sun_percent()
# logger.info("sun_percent == %s" % sun_percent)

# compass_image, compass_height, compass_width = navigation.get_compass_image(testing=False)
# screen.hsv_slider(bandw=True)

# compass_image, compass_height, compass_width = navigation.get_compass_image(testing=False)
# screen.hsv_slider(bandw=True)

# nav_point = navigation.get_navpoint_coordinates(testing=False)
# logger.info("navpoint_coordinates = %s" % nav_point)

# nav_check = navigation.check_coordinates(nav_point)
# logger.info("check_coordinates %s = %s" % (nav_point, nav_check))

# navpoint_offset = navigation.get_navpoint_offset()
# logger.info("navpoint_offset == %s" % navpoint_offset)

# center = {'x': 0, 'y': 0}
# direction = navigation.compare_coordinates(center, navpoint_offset)
# logger.info("direction = %s" % direction)

# dest_point = navigation.get_destination_coordinates(testing=False)
# logger.info("destination_coordinates = %s" % dest_point)

# dest_check = navigation.check_coordinates(dest_point)
# logger.info("check_coordinates %s = %s" % (dest_point, dest_check))

# destination_offset = navigation.get_destination_offset(testing=False)
# logger.info("destination_offset == %s" % destination_offset)

# center = {'x': 0, 'y': 0}
# direction = navigation.compare_coordinates(center, destination_offset)
# logger.info("direction = %s" % direction)

# navigation.navigation_align()
# navigation.destination_align()

# navigation.autopilot()

navigation.supercruise()

if hwnd:
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
        win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        logger.fatal(e)
