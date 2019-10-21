import logging
from math import degrees, atan
from random import random
from time import sleep, time

import colorlog
import cv2
from numpy import sum, where

from edcm import windows
from edcm.bindings import get_bindings, get_scanner
from edcm.control import send
from edcm.journal import get_ship_status
from edcm.screen import resource_path, filter_blue, filter_sun, get_elite_size, get_screen, equalize, \
    get_elite_cockpit_size, filter_orange

logger = colorlog.getLogger()

logger.setLevel(logging.INFO)

# SHIP_FACTOR = 1  # highly maneuverable small ships
SHIP_FACTOR = 2  # medium ships
# SHIP_FACTOR = 3  # large and slow handling

SCOOPABLE_STAR_TYPES = ['A', 'B', 'F', 'G', 'K', 'M', 'O']

keymap = get_bindings()

global same_last_count, last_last


def sun_percent():
    logger.info("sun_percent()")
    screen_size = get_elite_size()
    logger.debug("screen_size: left = %s, top = %s, width = %s, height = %s"
                 % (screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height']))

    # capture canopy view
    screen_size['left'] = round(int(screen_size['width']) * (1 / 3))
    screen_size['top'] = round(int(screen_size['height']) * (1 / 3))
    screen_size['width'] = round(int(screen_size['width']) * (2 / 3))
    screen_size['height'] = round(int(screen_size['height']) * (2 / 3))
    logger.debug("screen_size: left = %s, top = %s, width = %s, height = %s"
                 % (screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height']))
    screen = get_screen(screen_size)

    filtered = filter_sun(screen)
    white = sum(filtered == 255)
    black = sum(filtered != 255)
    logger.info("sun_percent = white {:.2f} / black {:.2f}".format(white, black))
    result = white / black * 100
    logger.info("sun_percent, return result %.2f" % result)
    return result


def get_compass_image(testing=False):
    logger.info("get_compass_image(testing=%s)" % testing)
    windows.set_elite_active_window()
    compass_template = cv2.imread(resource_path("..\\templates\\compass.png"), cv2.IMREAD_GRAYSCALE)
    compass_width, compass_height = compass_template.shape[::-1]
    doubt = 10
    while True:
        screen_size = get_elite_size()
        # locate compass by screen ratio
        # screen_size['left'] = round(int(screen_size['width']) * (5 / 16))
        # screen_size['top'] = round(int(screen_size['height']) * (5 / 8))
        screen_size['width'] = round(int(screen_size['width']) * (2 / 4))
        screen_size['height'] = round(int(screen_size['height']) * (15 / 16))
        hud_image = get_screen(screen_size)

        # mask_orange = filter_orange(hud_image)
        equalized = equalize(hud_image)
        match = cv2.matchTemplate(equalized, compass_template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.3
        loc = where(match >= threshold)
        pt = (doubt, doubt)
        for point in zip(*loc[::-1]):
            pt = point
        compass_image = hud_image[pt[1] - doubt: pt[1] + compass_height + doubt,
                        pt[0] - doubt: pt[0] + compass_width + doubt].copy()

        if testing:
            logger.debug("get_compass_image: cv2.imshow")
            cv2.rectangle(hud_image, pt, (pt[0] + compass_width, pt[1] + compass_height), (0, 0, 255), 2)
            cv2.imshow('Compass Template', compass_template)
            cv2.imshow('Compass Found', hud_image)
            cv2.imshow('Compass Mask', equalized)
            cv2.imshow('Compass', compass_image)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        else:
            break

    return compass_image, compass_width + (2 * doubt), compass_height + (2 * doubt)


def get_navpoint_offset(testing=False, last=None):
    logger.info("get_navpoint_offset(testing=%s, last=%s)" % (testing, last))
    global same_last_count, last_last
    navpoint_template = cv2.imread(resource_path("..\\templates\\navpoint.png"), cv2.IMREAD_GRAYSCALE)
    navpoint_width, navpoint_height = navpoint_template.shape[::-1]
    pt = (0, 0)
    while True:
        compass_image, compass_width, compass_height = get_compass_image()
        mask_blue = filter_blue(compass_image)
        #         filtered = filter_bright(compass_image)
        match = cv2.matchTemplate(mask_blue, navpoint_template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.5
        loc = where(match >= threshold)
        for point in zip(*loc[::-1]):
            pt = point
        final_x = (pt[0] + ((1 / 2) * navpoint_width)) - ((1 / 2) * compass_width)
        final_y = ((1 / 2) * compass_height) - (pt[1] + ((1 / 2) * navpoint_height))
        if testing:
            cv2.rectangle(compass_image, pt, (pt[0] + navpoint_width, pt[1] + navpoint_height), (0, 0, 255), 2)
            cv2.imshow('Navpoint Found', compass_image)
            cv2.imshow('Navpoint Mask', mask_blue)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        else:
            break
    if pt[0] == 0 and pt[1] == 0:
        if last:
            try:
                if last_last is not None and last == last_last:
                    same_last_count = same_last_count + 1
                else:
                    last_last = last
                    same_last_count = 0
                if same_last_count > 5:
                    same_last_count = 0
                    if random() < .9:
                        result = {'x': 1, 'y': 100}
                    else:
                        result = {'x': 100, 'y': 1}
                else:
                    result = last
            except NameError:
                logger.error("NameError, go back and try again.")
                logger.info("get_navpoint_offset(testing=%s, last=%s)" % (testing, last))
                return get_navpoint_offset(testing=testing, last=last)
        else:
            result = None
    else:
        result = {'x': final_x, 'y': final_y}
    logging.debug('get_navpoint_offset=' + str(result))
    return result


def get_destination_offset(testing=False):
    destination_template = cv2.imread(resource_path("..\\templates\\destination.png"), cv2.IMREAD_GRAYSCALE)
    destination_width, destination_height = destination_template.shape[::-1]
    pt = (0, 0)
    screen_size = get_elite_size()
    width = (1 / 3) * int(screen_size['width'])
    height = (1 / 3) * int(screen_size['height'])
    while True:
        screen = get_screen(get_elite_cockpit_size())
        mask_orange = filter_orange(screen)
        #         equalized = equalize(screen)
        match = cv2.matchTemplate(mask_orange, destination_template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.2
        loc = where(match >= threshold)
        for point in zip(*loc[::-1]):
            pt = point
        final_x = (pt[0] + ((1 / 2) * destination_width)) - ((1 / 2) * width)
        final_y = ((1 / 2) * height) - (pt[1] + ((1 / 2) * destination_height))
        if testing:
            cv2.rectangle(screen, pt, (pt[0] + destination_width, pt[1] + destination_height), (0, 0, 255), 2)
            cv2.imshow('Destination Found', screen)
            cv2.imshow('Destination Mask', mask_orange)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        else:
            break
    if pt[0] == 0 and pt[1] == 0:
        result = None
    else:
        result = {'x': final_x, 'y': final_y}
    logging.debug('get_destination_offset=' + str(result))
    return result


def x_angle(point=None):
    if not point:
        return None
    result = degrees(atan(point['y'] / point['x']))
    if point['x'] > 0:
        return +90 - result
    else:
        return -90 - result


def align():
    logger.info("align()")
    if not (get_ship_status()['status'] == 'in_supercruise' or get_ship_status()['status'] == 'in_space'):
        logger.error('align=err1')
        raise Exception('align error 1')

    logging.debug('align= speed 100')
    send(keymap['SetSpeed100'])

    logging.debug('align= avoid sun')
    while sun_percent() > 5:
        send(keymap['PitchUpButton'], state=1)
    send(keymap['PitchUpButton'], state=0)

    logging.debug('align= find navpoint')
    off = get_navpoint_offset()
    while not off:
        send(keymap['PitchUpButton'], state=1)
        off = get_navpoint_offset()
    send(keymap['PitchUpButton'], state=0)

    logging.debug('align= crude align')
    close = 3
    close_a = 18
    hold_pitch = 0.350 * SHIP_FACTOR
    hold_roll = 0.170 *  SHIP_FACTOR
    ang = x_angle(off)
    while (off['x'] > close and ang > close_a) or (off['x'] < -close and ang < -close_a) or (off['y'] > close) or (
            off['y'] < -close):

        while (off['x'] > close and ang > close_a) or (off['x'] < -close and ang < -close_a):

            if off['x'] > close and ang > close:
                send(keymap['RollRightButton'], hold=hold_roll)
            if off['x'] < -close and ang < -close:
                send(keymap['RollLeftButton'], hold=hold_roll)

            if get_ship_status()['status'] == 'starting_hyperspace':
                return
            off = get_navpoint_offset(last=off)
            ang = x_angle(off)

        ang = x_angle(off)
        while (off['y'] > close) or (off['y'] < -close):

            if off['y'] > close:
                send(keymap['PitchUpButton'], hold=hold_pitch)
            if off['y'] < -close:
                send(keymap['PitchDownButton'], hold=hold_pitch)

            if get_ship_status()['status'] == 'starting_hyperspace':
                return
            off = get_navpoint_offset(last=off)
            ang = x_angle(off)

        off = get_navpoint_offset(last=off)
        ang = x_angle(off)

    logging.debug('align= fine align')
    sleep(0.5)
    close = 50
    hold_pitch = 0.200 * SHIP_FACTOR
    hold_yaw = 0.400 * SHIP_FACTOR
    for i in range(5):
        new = get_destination_offset()
        if new:
            off = new
            break
        sleep(0.25)
    if not off:
        return
    while (off['x'] > close) or (off['x'] < -close) or (off['y'] > close) or (off['y'] < -close):

        if off['x'] > close:
            send(keymap['YawRightButton'], hold=hold_yaw)
        if off['x'] < -close:
            send(keymap['YawLeftButton'], hold=hold_yaw)
        if off['y'] > close:
            send(keymap['PitchUpButton'], hold=hold_pitch)
        if off['y'] < -close:
            send(keymap['PitchDownButton'], hold=hold_pitch)

        if get_ship_status()['status'] == 'starting_hyperspace':
            return

        for i in range(5):
            new = get_destination_offset()
            if new:
                off = new
                break
            sleep(0.25)
        if not off:
            return

    logging.debug('align=complete')


def jump():
    logging.debug('jump')
    tries = 3
    for i in range(tries):
        logging.debug('jump= try:' + str(i))
        if not (get_ship_status()['status'] == 'in_supercruise' or get_ship_status()['status'] == 'in_space'):
            logging.error('jump=err1')
            raise Exception('not ready to jump')
        sleep(0.5)
        logging.debug('jump= start fsd')
        send(keymap['HyperSuperCombination'], hold=1)
        sleep(16)
        if get_ship_status()['status'] != 'starting_hyperspace':
            logging.debug('jump= misaligned stop fsd')
            send(keymap['HyperSuperCombination'], hold=1)
            sleep(2)
            align()
        else:
            logging.debug('jump= in jump')
            while get_ship_status()['status'] != 'in_supercruise':
                sleep(1)
            logging.debug('jump= speed 0')
            send(keymap['SetSpeedZero'])
            logging.debug('jump=complete')
            return True
    logging.error('jump=err2')
    raise Exception("jump failure")


def refuel(refuel_threshold=33):
    logging.debug('refuel')

    if get_ship_status()['status'] != 'in_supercruise':
        logging.error('refuel=err1')
        return False

    if get_ship_status()['fuel_percent'] < refuel_threshold and get_ship_status()['star_class'] in SCOOPABLE_STAR_TYPES:
        logging.debug('refuel= start refuel')
        send(keymap['SetSpeed100'])
        #     while not get_ship_status()['is_scooping']:
        #         sleep(1)
        sleep(4)
        logging.debug('refuel= wait for refuel')
        send(keymap['SetSpeedZero'], repeat=3)
        while not get_ship_status()['fuel_percent'] == 100:
            sleep(1)
        logging.debug('refuel=complete')
        return True
    elif get_ship_status()['fuel_percent'] >= refuel_threshold:
        logging.debug('refuel= not needed')
        return False
    elif get_ship_status()['star_class'] not in SCOOPABLE_STAR_TYPES:
        logging.debug('refuel= needed, unsuitable star')
        return False
    else:
        return False


def position(refueled_multiplier=1):
    logging.debug('position')
    logging.debug('position=scanning')
    send(keymap[get_scanner()], state=1)
    send(keymap['PitchUpButton'], state=1)
    sleep(5)
    send(keymap['PitchUpButton'], state=0)
    send(keymap['SetSpeed100'])
    send(keymap['PitchUpButton'], state=1)
    while sun_percent() > 3:
        sleep(1)
    sleep(5)
    send(keymap['PitchUpButton'], state=0)
    sleep(5 * refueled_multiplier)
    logging.debug('position=scanning complete')
    send(keymap[get_scanner()], state=0)
    logging.debug('position=complete')
    return True


def auto_launch():
    logging.debug("auto_undock()")
    ship_status = get_ship_status()['status']
    if ship_status == 'in_station':
        send(keymap['UI_Down'], repeat=2)  # UI move down to AUTO LAUNCH
        send(keymap['UI_Select'])
        logging.debug("Auto Launch in progress.")
        t0 = time()
        t1 = time()
        last = t0
        # wait til ship status change
        while ship_status in ('in_station', 'in_docking', 'docking', 'in_undocking'):
            sleep(.2)  # cpu friendly spin
            t1 = time()
            ship_status = get_ship_status()['status']
            if last - t1 > 5:
                last = t1
                logger.debug("t- %.2f, ship_status = %s" % ((t1 - t0), get_ship_status()['status']))
        logger.info(">>> AUTO LAUNCH completed in %.2f seconds" % (t1 - t0))
        # boost 3x away
        for i in range(3):
            send(keymap['UseBoostJuice'])
            send(keymap['IncreaseEnginesPower'], repeat=3, repeat_delay=.1)
            sleep(7)
            send(keymap['ResetPowerDistribution'])
    logger.debug("auto_launch() completed.")


def autopilot():
    logging.info('\n' + 200 * '-' + '\n' + '---- AUTOPILOT START ' + 179 * '-' + '\n' + 200 * '-')
    logging.debug('ship=' + str(get_ship_status()))
    while get_ship_status()['target']:
        if get_ship_status()['status'] == 'in_space' or get_ship_status()['status'] == 'in_supercruise':
            logging.info('\n' + 200 * '-' + '\n' + '---- AUTOPILOT ALIGN ' + 179 * '-' + '\n' + 200 * '-')
            align()
            logging.info('\n' + 200 * '-' + '\n' + '---- AUTOPILOT JUMP ' + 180 * '-' + '\n' + 200 * '-')
            jump()
            logging.info('\n' + 200 * '-' + '\n' + '---- AUTOPILOT REFUEL ' + 178 * '-' + '\n' + 200 * '-')
            refueled = refuel()
            logging.info('\n' + 200 * '-' + '\n' + '---- AUTOPILOT POSIT ' + 179 * '-' + '\n' + 200 * '-')
            if refueled:
                position(refueled_multiplier=4)
            else:
                position(refueled_multiplier=1)
    send(keymap['SetSpeedZero'])
    logging.info('\n' + 200 * '-' + '\n' + '---- AUTOPILOT END ' + 181 * '-' + '\n' + 200 * '-')
