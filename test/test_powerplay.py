import logging
import os
import sys
import win32gui
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from edcm import windows
from edcm import powerplay
from edcm import galaxy_map
from edcm import navigation


logger = logging.getLogger(__name__)

print(sys.path)

hwnd = windows.get_my_hwnd()
windows.print_hwnd_info(hwnd)

elite_hwnd = windows.get_elite_hwnd()
windows.print_hwnd_info(elite_hwnd)

print("Elite Dangerous is active window...")
win32gui.SetForegroundWindow(elite_hwnd)


# TEST #

# START DOCKED AT POWER PLAY CONTROL STATION #
powerplay.fast_load_forts()


# SET DESTINATION TO POWER PLAY FORTIFICATION SYSTEM
galaxy_map.set_destination("ALLOWINI")

navigation.auto_launch()

navigation.autopilot()

# navigation.supercurise()

print("Return to original window")
if hwnd:
    win32gui.SetForegroundWindow(hwnd)
