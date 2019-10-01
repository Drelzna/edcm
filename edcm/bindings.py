import os

import glob
from xml.etree.ElementTree import parse
import colorlog
import logging
from edcm.directinput import SCANCODE

logging.basicConfig(filename='edcm.log', level=logging.DEBUG)
logger = colorlog.getLogger()
logger.setLevel(logging.DEBUG)


# static config
KEYBIND = "Development.3.0.binds"

SCAN = 2  # set discovery scanner fire group mapping to 1 = PrimaryFire or 2 = SecondaryFire

DEFAULT_BINDING_PATH = os.path.join(
        os.environ['LOCALAPPDATA'],
        'Frontier Developments',
        'Elite Dangerous',
        'Options',
        'Bindings')

REQUIRED_KEYS = [
    'YawLeftButton',
    'YawRightButton',
    'RollLeftButton',
    'RollRightButton',
    'PitchUpButton',
    'PitchDownButton',
    'SetSpeedZero',
    'SetSpeed100',
    'HyperSuperCombination',
    'GalaxyMapOpen',
    'UIFocus',
    'UI_Up',
    'UI_Down',
    'UI_Left',
    'UI_Right',
    'UI_Select',
    'UI_Back',
    'CycleNextPanel',
    'HeadLookReset',
    'SelectTarget',
    'PrimaryFire',
    'SecondaryFire'
]


def get_latest_bindings(bind_file=KEYBIND):
    """
    Return the most recently modified Elite Dangerous Control Bindings file
    :param :bind_file
    :return: File
    """
    logger.info("get_latest_bindings()")
    path_to_keybindings = DEFAULT_BINDING_PATH
    logger.info("get_latest_bindings: path_to_keybindings=" + path_to_keybindings)
    bind_files = glob.glob(path_to_keybindings + os.path.sep + '*.binds')
    logger.info("bind_files = " + str(bind_files))
    for f in bind_files:
        logger.info("get_latest_bindings: scanning bind file " + f)
        if f.endswith(bind_file):
            logger.info("FOUND: " + f)
            return f

    list_of_bindings = [os.path.join(path_to_keybindings, f) for f in bind_files
                        if os.path.isfile(os.path.join(path_to_keybindings, f))]
    latest_bindings = max(list_of_bindings, key=os.path.getmtime)
    logger.info("get_latest_bindings: latest_bindings=" + latest_bindings)
    return latest_bindings


def get_bindings(bind_file=KEYBIND):
    """
    returns a dictionary of EliteDangerous key bindings mapped to DirectInput keys
    :param :bind_file
    :return: dict containing eliteDangerous key -> directinput key
    """
    direct_input_keys = {}
    convert_to_direct_keys = {
        'Key_LeftShift': 'LShift',
        'Key_RightShift': 'RShift',
        'Key_LeftAlt': 'LAlt',
        'Key_RightAlt': 'RAlt',
        'Key_LeftControl': 'LControl',
        'Key_RightControl': 'RControl'
    }

    latest_bindings = get_latest_bindings(bind_file)
    bindings_tree = parse(latest_bindings)
    bindings_root = bindings_tree.getroot()

    for item in bindings_root:
        if item.tag in REQUIRED_KEYS:
            key = None
            mod = None
            # Check primary
            if item[0].attrib['Device'].strip() == "Keyboard":
                key = item[0].attrib['Key']
                if len(item[0]) > 0:
                    mod = item[0][0].attrib['Key']
            # Check secondary (and prefer secondary)
            if item[1].attrib['Device'].strip() == "Keyboard":
                key = item[1].attrib['Key']
                if len(item[1]) > 0:
                    mod = item[1][0].attrib['Key']
            # Adequate key to SCANCODE dict standard
            if key in convert_to_direct_keys:
                key = convert_to_direct_keys[key]
            elif key is not None:
                key = key[4:]
            # Adequate mod to SCANCODE dict standard
            if mod in convert_to_direct_keys:
                mod = convert_to_direct_keys[mod]
            elif mod is not None:
                mod = mod[4:]
            # Prepare final binding
            binding = None
            if key is not None:
                binding = {'pre_key': 'DIK_' + key.upper()}
                binding['key'] = SCANCODE[binding['pre_key']]
                if mod is not None:
                    binding['pre_mod'] = 'DIK_' + mod.upper()
                    binding['mod'] = SCANCODE[binding['pre_mod']]
            if binding is not None:
                direct_input_keys[item.tag] = binding

    # bind escape key
    esc_binding = {'pre_key': 'DIK_ESCAPE'}
    esc_binding['key'] = SCANCODE[esc_binding['pre_key']]
    direct_input_keys['ESC'] = esc_binding

    # bind return key
    return_binding = {'pre_key': 'DIK_RETURN'}
    return_binding['key'] = SCANCODE[return_binding['pre_key']]
    direct_input_keys['RET'] = return_binding

    # mouse bindings
    primary_fire = {'pre_key': 'DIK_ADD'}
    primary_fire['key'] = SCANCODE[primary_fire['pre_key']]
    secondary_fire = {'pre_key': 'DIK_NUMPADENTER'}
    secondary_fire['key'] = SCANCODE[secondary_fire['pre_key']]
    direct_input_keys['PrimaryFire'] = primary_fire
    direct_input_keys['SecondaryFire'] = secondary_fire


    if len(list(direct_input_keys.keys())) < 1:
        return None
    else:
        return direct_input_keys


def get_scanner():
    if SCAN == 1:
        return 'PrimaryFire'
    elif SCAN == 2:
        return 'SecondaryFire'
    else:
        return False