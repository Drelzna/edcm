import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from time import sleep
from edcm import galaxy_map

sleep(5)
galaxy_map.set_destination("SIRIUS")

