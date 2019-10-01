import os
import sys

import colorlog

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from edcm import journal

logger = colorlog.getLogger()

j = journal.get_latest_journal()
assert j is not None
logger.info("Current Player Journal: %s " % j)

ship_status = journal.get_ship_status()
assert ship_status is not None

logger.info("ship_status:\n"
            "time = %s\n"
            "type = %s\n"
            "location = %s\n"
            "star_class = %s\n"
            "target = %s\n"
            "fuel_capacity = %s\n"
            "fuel_level = %s\n"
            "fuel_percent = %s\n"
            "is_scooping = %s\n" %
            (ship_status['time'],
             ship_status['type'],
             ship_status['location'],
             ship_status['star_class'],
             ship_status['target'],
             ship_status['fuel_capacity'],
             ship_status['fuel_level'],
             ship_status['fuel_percent'],
             ship_status['is_scooping']))
