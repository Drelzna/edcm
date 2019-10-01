import logging
import colorlog
from time import sleep
from edcm.directinput import SCANCODE
from edcm.bindings import get_bindings
from edcm.control import send

logging.basicConfig(filename='edcm.log', level=logging.DEBUG)
logger = colorlog.getLogger()
logger.setLevel(logging.DEBUG)


keymap =  get_bindings()

def open_galaxy_map():
    logger.info("open_galaxy_map()")
    send(keymap['GalaxyMapOpen'])


def close_galaxy_map():
    open_galaxy_map()


def set_destination(destination_system="Sol"):
    open_galaxy_map()
    sleep(5)

    # select current location
    send(keymap['CycleNextPanel'])
    send(keymap['UI_Left'])
    send(keymap['UI_Down'])
    send(keymap['UI_Select'])

    # select search box
    send(keymap['UI_Left'])
    send(keymap['UI_Up'])
    send(keymap['UI_Select'])  # select SEARCH Box

    # type dest string in search box followed by return
    for c in destination_system:
        direct_key = {}
        direct_key['key'] = SCANCODE["DIK_" + c.upper()]
        send(direct_key)
        sleep(.1)
    send(keymap['RET'])

    sleep(10)  # plotting route time

    # select route
    send(keymap['UI_Select'])
    send(keymap['UI_Right'])
    send(keymap['UI_Select'])

    sleep(1)
    close_galaxy_map()





