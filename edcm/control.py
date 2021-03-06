import logging
from time import sleep
from edcm.directinput import press_key, release_key

logger = logging.getLogger(__name__)

KEY_MOD_DELAY = 0.010
KEY_DEFAULT_DELAY = 0.200
KEY_REPEAT_DELAY = 0.100
FUNCTION_DEFAULT_DELAY = 0.500


def send(key, hold=None, repeat=1, repeat_delay=None, state=None):
    """
    send() interface to directkey pressKey and releaseKey methods

    :param key: The DirectKey to Press
    :param hold: pressKey, sleep for 'hold' seconds, releaseKey
    :param repeat: repeat pressKey and releaseKey 'repeat' times
    :param repeat_delay: wait 'repeat_delay' seconds per repeat loop
    :param state: 1 = pressKey, 2 = releaseKey
    :return:
    """
    global KEY_MOD_DELAY, KEY_DEFAULT_DELAY, KEY_REPEAT_DELAY

    if key is None:
        logging.warning('send(key), key = None ... returning')
        return

    logging.debug(
        'send=key:' + str(key) +
        ',hold:' + str(hold) +
        ',repeat:' + str(repeat) +
        ',repeat_delay:' + str(repeat_delay) +
        ',state:' + str(state))

    for i in range(repeat):

        if state is None or state == 1:
            if 'mod' in key:
                press_key(key['mod'])
                sleep(KEY_MOD_DELAY)

            press_key(key['key'])

        if state is None:
            if hold:
                sleep(hold)
            else:
                sleep(KEY_DEFAULT_DELAY)

        if state is None or state == 0:
            release_key(key['key'])

            if 'mod' in key:
                sleep(KEY_MOD_DELAY)
                release_key(key['mod'])

        if repeat_delay:
            sleep(repeat_delay)
        else:
            sleep(KEY_REPEAT_DELAY)
