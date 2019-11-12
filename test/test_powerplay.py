import sys
import os
import logging
import colorlog
import win32gui

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from edcm import windows
from edcm import powerplay
from edcm import galaxy_map
from edcm import navigation

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

hwnd = windows.get_my_hwnd()
windows.print_hwnd_info(hwnd)

elite_hwnd = windows.get_elite_hwnd()
windows.print_hwnd_info(elite_hwnd)

print("Elite Dangerous is active window...")
win32gui.SetForegroundWindow(elite_hwnd)

# TEST #

# START DOCKED AT POWER PLAY CONTROL STATION #
powerplay.load(cargo_type="fort", fast_track=True)
# powerplay.load(cargo_type="prep",fast_track=True)


# SET DESTINATION TO POWER PLAY FORTIFICATION SYSTEM
galaxy_map.set_destination("DONGKUM")

navigation.auto_launch()

navigation.autopilot()

navigation.supercruise()

print("Return to original window")
if hwnd:
    win32gui.SetForegroundWindow(hwnd)
