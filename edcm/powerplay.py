import logging
from edcm import menu
from edcm import journal
from edcm.bindings import get_bindings
from edcm.control import send
import json
from time import sleep

logger = logging.getLogger(__name__)

keymap = get_bindings()


def get_forts(fast_track=False):
    # start at docked station menu
    # TODO: from edcm import text.get_screen_text
    #       if screen_text matches 'STARPORT SERVICES'
    logger.info("get_forts() starting")
    logger.debug("UI_select on 'STARPORT SERVICES'")
    send(keymap['UI_Select'])  # select 'STARPORT SERVICES'
    sleep(2.7)

    # move up to contacts
    send(keymap['UI_Up'], repeat=3, repeat_delay=.5)  # move to CONTACTS
    logger.debug("UI_select on 'CONTACTS'")
    send(keymap['UI_Select'])  # select 'CONTACTS'
    sleep(2.3)

    send(keymap['UI_Right'], repeat=2, repeat_delay=.5)  # move to COMBAT BOND CONTACT
    send(keymap['UI_Down'])  # move to POWER CONTACT
    send(keymap['UI_Select'])  # select 'POWER CONTACT'
    sleep(2.3)

    # customize for the specific power play panel
    # hudson, down 1, 'collect hudson garrison supplies'
    send(keymap['UI_Down'])  # move to collect

    # hold down UI_Right for 30 seconds
    if fast_track:
        send(keymap['UI_Select'])  # FAST TRACK QUOTA FOR CREDITS
        sleep(5.1)

    logger.info("hold 'collect' for 15 seconds")
    send(keymap['UI_Right'], hold=15)  # move to collect
    send(keymap['UI_Select'])  # CONFIRM
    sleep(2.3)

    send(keymap['UI_Select'])  # BACK TO MAIN PAGE

    send(keymap['UI_Left'])  # move to collect
    send(keymap['UI_Select'])  # BACK
    sleep(.3)

    send(keymap['UI_Left'])  # move to collect
    send(keymap['UI_Select'])  # BACK
    sleep(.3)

    send(keymap['UI_Up'])  # move to EXIT
    send(keymap['UI_Select'])  # EXIT STARPORT SERVICES
    sleep(2.3)

    logger.info("get_forts() completed.")


def get_preps(fast_track=False):
    # start at docked station menu
    # TODO: from edcm import text.get_screen_text
    #       if screen_text matches 'STARPORT SERVICES'
    logger.info("get_forts() starting")
    logger.debug("UI_select on 'STARPORT SERVICES'")
    send(keymap['UI_Select'])  # select 'STARPORT SERVICES'
    sleep(2.7)

    # move up to contacts
    send(keymap['UI_Up'], repeat=3, repeat_delay=.5)  # move to CONTACTS
    logger.debug("UI_select on 'CONTACTS'")
    send(keymap['UI_Select'])  # select 'CONTACTS'
    sleep(1.3)

    send(keymap['UI_Right'], repeat=2, repeat_delay=.5)  # move to COMBAT BOND CONTACT
    send(keymap['UI_Down'], repeat=2, repeat_delay=.5)  # move to POWER CONTACT
    send(keymap['UI_Select'])  # select 'POWER CONTACT'
    sleep(1.3)

    # customize for the specific power play panel
    # hudson, down 1, 'collect hudson garrison supplies'
    send(keymap['UI_Down'], repeat=2, repeat_delay=.5)  # move to collect

    # hold down UI_Right for 30 seconds
    if fast_track:
        send(keymap['UI_Select'])  # FAST TRACK QUOTA FOR CREDITS
        sleep(5.1)

    logger.info("hold 'collect' for 15 seconds")
    send(keymap['UI_Right'], hold=10)  # move to collect
    send(keymap['UI_Select'])  # CONFIRM
    sleep(1.3)

    send(keymap['UI_Select'])  # BACK TO MAIN PAGE

    send(keymap['UI_Left'])  # move to collect
    send(keymap['UI_Select'])  # BACK
    sleep(.3)

    send(keymap['UI_Left'])  # move to collect
    send(keymap['UI_Select'])  # BACK
    sleep(.3)

    send(keymap['UI_Up'])  # move to EXIT
    send(keymap['UI_Select'])  # EXIT STARPORT SERVICES
    sleep(2.3)

    logger.info("get_preps() completed.")


def load(cargo_type="fort", fast_track=False):
    status = journal.get_ship_status()
    logger.info(json.dumps(status))
    cargo = int(status['cargo_count'])
    max_cargo = int(status['cargo_capacity'])
    space_available = max_cargo - cargo

    while space_available > 0:
        logger.info("cargo (used) = %f" % cargo)
        logger.info("cargo (capacity) = %f" % max_cargo)
        logger.info("cargo (free) = %f" % space_available)

        if str(cargo_type).endswith("ort"):
            get_forts(fast_track=fast_track)
        else:
            get_preps(fast_track=fast_track)

        status = journal.get_ship_status()
        cargo = int(status['cargo_count'])
        max_cargo = int(status['cargo_capacity'])
        space_available = max_cargo - cargo

        if not fast_track:
            menu.exit_to_main_menu()
            sleep(1800)  # 30 minutes
            menu.start_solo()
