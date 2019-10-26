import logging

import colorlog

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


# SHIP_FACTOR = 1  # highly maneuverable small ships
SHIP_FACTOR = 2  # medium ships
# SHIP_FACTOR = 3  # large and slow handling
