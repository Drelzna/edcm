import logging
from time import sleep
from edcm.bindings import get_bindings
from edcm.control import send

logger = logging.getLogger(__name__)

keymap =  get_bindings()

def exit_to_main_menu(wait=None):
    logger.info("exit_to_main_menu()")
    send(keymap['ESC'])
    send(keymap['UI_Down'])
    send(keymap['UI_Down'])
    send(keymap['UI_Down'])
    send(keymap['UI_Down'])
    send(keymap['UI_Down'])  # 2019-09-19 'BUY ARX'
    send(keymap['UI_Select'])
    sleep(5)
    if wait:
        sleep(15)  # 15 second logout timer
    send(keymap['UI_Right'])
    send(keymap['UI_Select'])
    sleep(35)
    logger.debug("completed exit_to_main()")


def start_open():
    logger.info("start_open")
    sleep(5)
    send(keymap['UI_Select'])
    send(keymap['UI_Select'])
    sleep(35)
    logger.debug("completed start_open()")


def start_solo():
    logger.info("start_solo")
    sleep(5)
    send(keymap['UI_Select'])
    send(keymap['UI_Right'])
    send(keymap['UI_Right'])
    send(keymap['UI_Select'])
    sleep(35)
    logger.debug("completed start_solo()")
