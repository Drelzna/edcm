import logging
from time import sleep
from edcm.directinput import SCANCODE
from edcm.bindings import get_bindings
from edcm.control import send
from edcm.journal import get_ship_status

logger = logging.getLogger(__name__)

keymap = get_bindings()


def open_galaxy_map():
    logger.info("open_galaxy_map()")
    send(keymap['GalaxyMapOpen'])


def close_galaxy_map():
    open_galaxy_map()


def set_destination(destination_system="Sol"):
    logger.info("set_destination(desination_system=%s)" % destination_system)
    ship_status = get_ship_status()
    logging.info("edcm.navigation.autopilot: ship_status = %s" % ship_status)
    if not ship_status['target']:
        logger.debug("destination system not set")
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

        # type destination string in search box followed by return
        for c in destination_system:
            logger.debug("destination_system: %s, character %s, ascii value: %s", destination_system, c, ord(c))
            if c.isspace() or ord(c) == 32:
                direct_key = {'key': SCANCODE["DIK_SPACE"]}
            elif ord(c) == 45:
                direct_key = {'key': SCANCODE["DIK_MINUS"]}
            else:
                direct_key = {'key': SCANCODE["DIK_" + c.upper()]}
            send(direct_key)
        send(keymap['RET'])

        sleep(3)  # estimate plotting route time, should be a screen read loop

        # select route
        send(keymap['UI_Select'])
        send(keymap['UI_Right'])
        send(keymap['UI_Select'])

        sleep(1)
        close_galaxy_map()
