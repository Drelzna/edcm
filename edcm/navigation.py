import json
import logging
from math import degrees, atan
from time import sleep, time

import cv2
import imutils
from numpy import sum, where, linspace, dstack

from edcm import windows
from edcm.bindings import get_bindings, get_scanner
from edcm.control import send
from edcm.journal import get_ship_status
from edcm.screen import resource_path, show_image, filter_sun, \
    get_elite_size, get_screen, equalize, filter_destination

logger = logging.getLogger(__name__)

# SHIP_FACTOR = 1  # highly maneuverable small ships
# SHIP_FACTOR = 1.5  # medium ships
# SHIP_FACTOR = 2  # medium ships
# SHIP_FACTOR = 3  # large and slow ships
SHIP_FACTOR = 2.2  # CUTTER

FUEL_STARS = ['A', 'B', 'F', 'G', 'K', 'M', 'O']

keymap = get_bindings()


def sun_percent():
    logger.info("edcm.navigation.sun_percent()")
    screen_size = get_elite_size()
    logger.info("screen_size: left = %s, top = %s, width = %s, height = %s"
                % (screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height']))

    # capture canopy view
    screen_size['left'] = round(int(screen_size['width']) * (1 / 3))
    screen_size['top'] = round(int(screen_size['height']) * (1 / 3))
    screen_size['width'] = round(int(screen_size['width']) * (2 / 3))
    screen_size['height'] = round(int(screen_size['height']) * (2 / 3))
    logger.info("screen_size: left = %s, top = %s, width = %s, height = %s"
                % (screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height']))
    screen = get_screen(screen_size)

    filtered = filter_sun(screen)
    white = sum(filtered == 255)
    black = sum(filtered != 255)
    logger.info("edcm.navigation.sun_percent: white = {:.2f} / black = {:.2f}".format(white, black))
    result = white / black * 100
    logger.info("edcm.navigation.sun_percent: return result %.2f" % result)
    return result


def get_compass_image(testing=False):
    logger.info("edcm.navigation.get_compass_image(testing=%s)" % testing)

    # left and top coordinate point for matched compass template
    pt = None

    match = None

    # additional pixels to match boundary
    doubt = 10

    windows.set_elite_active_window()

    # read high resolution navigation compass template from disk
    # compass_file = cv2.imread(resource_path("..\\templates\\navcompass.jpg"), 1)
    compass_file = cv2.imread(resource_path("..\\templates\\navcircle.png"), 1)
    # compass_file = cv2.imread(resource_path("..\\templates\\navcompass.png"), 1)
    # compass_file = cv2.imread(resource_path("..\\templates\\compass.png"), 1)
    compass_template = cv2.cvtColor(compass_file, cv2.COLOR_BGR2GRAY)
    (compass_width, compass_height) = compass_template.shape[::-1]
    logger.debug("compass_template: width, height, channels: %s, %s" % (compass_width, compass_height))

    screen_size = get_elite_size()
    logger.info("screen_size: left = %s, top = %s, width = %s, height = %s"
                % (screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height']))

    # Take screenshot, reduce size to compass location by screen ratio
    compass_screen = {'left': round(int(screen_size['width'] * 5 / 16)),
                      'top': round(int(screen_size['height'] * 1 / 2)),
                      'width': round(int(screen_size['width'] * 1 / 2)),
                      'height': round(int(screen_size['height'] * 1 / 2))}
    # screen_size['top'] = screen_size['height'] - round(int(screen_size['height'] * 1/3))
    # screen_size['height'] = round(int(screen_size['height'] * 1/3))
    logger.info("compass_screen: left = %s, top = %s, width = %s, height = %s"
                % (compass_screen['left'], compass_screen['top'], compass_screen['width'], compass_screen['height']))
    compass_image = get_screen(compass_screen, color="GRAY")
    if testing:
        logger.info("show_image(compass_image")
        show_image(compass_image)

    compass_template = cv2.Canny(compass_template, 100, 200)
    if testing:
        logger.info("show_image(compass_template)")
        show_image(compass_template)

    # check for match
    logger.debug("match = cv2.matchTemplate(compass_image, compass_template, cv2.TM_CCOEFF)")
    match = cv2.matchTemplate(compass_image, compass_template, cv2.TM_CCOEFF)
    logger.debug(match)
    # failed 1:1 match, attempt to rescale, template must be larger than capture
    if match is None:
        # loop over the scales of the image
        for scale in linspace(0.2, 1.0, 20)[::-1]:
            # resize the captured compass_image according to the scale, and keep track
            # of the ratio of the resizing
            resized = imutils.resize(compass_image, width=int(compass_image.shape[1] * scale))
            r = compass_image.shape[1] / float(resized.shape[1])
            # if the resized image is smaller than the template, then break
            # from the loop
            if resized.shape[0] < compass_height or resized.shape[1] < compass_width:
                break
            # detect edges in the resized, grayscale image and apply template
            # matching to find the template in the image
            edged = cv2.Canny(compass_image, 50, 200)
            match = cv2.matchTemplate(edged, compass_template, cv2.TM_CCOEFF)
            threshold = 0.8
            loc = np.where(match >= threshold)
            (_, maxVal, _, maxLoc) = cv2.minMaxLoc(match)

            if testing:
                # draw a bounding box around the detected region
                clone = dstack([edged, edged, edged])
                cv2.rectangle(clone, (maxLoc[0], maxLoc[1]),
                              (maxLoc[0] + compass_width, maxLoc[1] + compass_height), (0, 0, 255), 2)
                show_image(clone)

            # if we have found a new maximum correlation value, then update
            # the bookkeeping variable
            if pt is None or maxVal > pt[0]:
                pt = (maxVal, maxLoc, r)

            # unpack the bookkeeping variable and compute the (x, y) coordinates
            # of the bounding box based on the resized ratio
            (_, maxLoc, r) = pt
            (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
            (endX, endY) = (int((maxLoc[0] + compass_width) * r), int((maxLoc[1] + compass_height) * r))
            # draw a bounding box around the detected result and display the image
            cv2.rectangle(compass_image, (startX, startY), (endX, endY), (0, 0, 255), 2)

            if testing:
                show_image(compass_image)

    # threshold = .4
    # logger.info("edcm.navigation.get_compass_image: match: %s >= threshold: %s" % (match, threshold))
    # loc = where(match >= threshold)
    # for point in zip(*loc[::-1]):
    #   pt = point
    #     cv2.rectangle(compass_image, pt, (pt[0] + compass_width, pt[1] + compass_height), (0, 0, 255), 2)

    # if testing:
    #     logger.info("show_image(match_image)")
    #     show_image(match_image)

    if pt is not None:
        compass_match = compass_image[
                        pt[1] - doubt: pt[1] + compass_height + doubt, pt[0] - doubt: pt[0] + compass_width + doubt
                        ].copy()

        if testing:
            logger.info("show_image(compass_match)")
            show_image(compass_match)
        return compass_match, compass_width + (2 * doubt), compass_height + (2 * doubt)
    else:
        logger.error("edcm.navigation.get_compass_image() failed.")

    return [None, None, None]


def get_image_match(image, template):
    match = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match)
    logger.info("edcm.navigation.get_image_match: match = (%s, %s, %s, %s)" % (min_val, max_val, min_loc, max_loc))
    return match


def check_reverse(compass_image, testing=False):
    logger.info("edcm.navigation.check_reverse(compass_image,testing=%s)" % testing)

    coordinates = None

    navcircle_template = cv2.imread(resource_path("..\\templates\\navcompass.png"), cv2.IMREAD_GRAYSCALE)
    navpoint_width, navpoint_height = navcircle_template.shape[::-1]
    equalized = equalize(compass_image)

    match = get_image_match(equalized, navcircle_template)
    match_image = compass_image.copy()
    threshold = 0.7

    loc = where(match >= threshold)
    for point in zip(*loc[::-1]):
        coordinates = point
        if testing:
            cv2.rectangle(match_image, coordinates,
                          (coordinates[0] + navpoint_width,
                           coordinates[1] + navpoint_height),
                          (0, 0, 255), 2)

    if testing:
        show_image(match_image)

    if coordinates is not None:
        logger.info("edcm.navigation.check_reverse() found coordinates: %s" % str(coordinates))
        return coordinates
    else:
        logger.info("edcm.navigation.check_reverse() no coordinates, return None")
        return False


def reverse_direction():
    logging.info("edcm.navigation.reverse_direction()")

    facing_forward = False

    handling = 2 + (2 * SHIP_FACTOR)
    if get_ship_status()['status'] == 'in_space':
        handling = handling * .5

    while not facing_forward:
        logger.info("edcm.navigation.reverse_direction: not facing_forward")
        logger.info("edcm.navigation.reverse_direction: SetSpeed50 ")
        send(keymap['SetSpeed50'])
        logger.info("edcm.navigation.reverse_direction: PitchUp (on)")
        send(keymap['PitchUpButton'], state=1)
        logger.info("edcm.navigation.reverse_direction: sleep(%.2f)" % handling)
        sleep(handling)
        logger.info("edcm.navigation.reverse_direction: PitchUp (off)")
        send(keymap['PitchUpButton'], state=0)
        compass_image, compass_width, compass_height = get_compass_image()
        if not check_reverse(compass_image, testing=False):
            facing_forward = True
        send(keymap['SetSpeed100'])


def get_navpoint_coordinates(testing=False):
    logger.info("edcm.navigation.get_navpoint_coordinates()")

    compass_image, compass_width, compass_height = get_compass_image()
    if check_reverse(compass_image):
        logger.warning("Matched NavCircle, must turn around")
        reverse_direction()
        return None

    logger.info("edcm.navigation.get_navpoint_coordinates: compass_height, compass_width = %.2f, %.2f" % (
        compass_height, compass_height))
    center = {'x': round(int(compass_width) * .5), 'y': round(int(compass_height) * .5)}
    logger.info("edcm.navigation.get_navpoint_coordinates: center = %s" % center)
    coordinates = None

    navball_template = cv2.imread(resource_path("..\\templates\\navball.png"), cv2.IMREAD_GRAYSCALE)
    navball_width, navball_height = navball_template.shape[::-1]

    # compass_image = filter_compass(compass_image)
    compass_image = equalize(compass_image)
    match = get_image_match(compass_image, navball_template)

    threshold = 0.8
    loc = where(match >= threshold)
    logger.info("edcm.navigation.get_navpoint_coordinates: loc = where(match >= threshold), %s = where(%s >= %s)" % (
        loc, match, threshold))
    mc = 0
    for point in zip(*loc[::-1]):
        mc += 1
        coordinates = point
        logger.info("edcm.navigation.get_navpoint_coordinates: coordinates = %s" % str(coordinates))
        if testing:
            cv2.rectangle(compass_image, coordinates,
                          (coordinates[0] + navball_width, coordinates[1] + navball_height), (0, 0, 255), 2)

    logger.info("edcm.navigation.get_navpoint_coordinates: match count = %i" % mc)

    if testing:
        show_image(compass_image)

    if coordinates is not None:
        logger.info("edcm.navigation.get_navpoint_coordinates: "
                    "final_x = ( coordinates[x] + ( navball_width * .5 )) - (compass_width * .5 ) ")
        logger.info("edcm.navigation.get_navpoint_coordinates: "
                    "final_x = ( %.2f + ( %.2f * .5 ) - ( %.2f * .5 )) " %
                    (coordinates[0], navball_width, compass_width))
        final_x = (coordinates[0] + (navball_width * .5)) - (compass_width * .5)

        logger.info("edcm.navigation.get_navpoint_coordinates: "
                    "final_y = ( ( compass_height * .5 ) - ( coordinates['y'] + (navball_height * .5 )) ")
        logger.info("edcm.navigation.get_navpoint_coordinates: "
                    "final_y = ( %.2f * .5 ) - ( %.2f + ( %.2f * .5 )) " %
                    (compass_height, coordinates[1], navball_height))
        final_y = (compass_height * .5) - (coordinates[1] + (navball_height * .5))

        return {'x': final_x, 'y': final_y}
    else:
        logger.error("failed to identify coordinates.")
        return None


def check_coordinates(point):
    logger.info("edcm.navigation.check_coordinates(point=%s)" % point)
    if point is not None:
        if 'x' not in point:
            logger.error("no 'x' in point")
            return False
        if 'y' not in point:
            logger.error("no 'y' in point")
            return False
        if point['x'] is None:
            logger.error("point['x'] is None")
            return False
        if point['y'] is None:
            logger.error("point['y'] is None")
            return False
    logger.info("edcm.navigation.check_coordinates() return True")
    return True


def compare_coordinates(point_a, point_b, threshold=3):
    """
    given 2 coordinate points on a cartesian plane,
    return a list of instructions to move toward center

    :param point_a: starting point
    :param point_b: destination point
    :param threshold: margin of error
    :return: list of directions in the form of:
     [UP/DOWN/LEFT/RIGHT] [relative distance]
     UP 3.5
     LEFT 23.203
     RIGHT 6.2
     DOWN 10
     ON
    """
    logger.info("edcm.navigation.compare_coordinates(point_a=%s, point_b=%s, threshold=%s)" % (
        str(point_a), str(point_b), threshold))
    direction = []

    # LEFT/RIGHT
    logger.info("point_a[x] = %.f" % point_a['x'])
    logger.info("point_b[x] = %.f" % point_b['x'])
    if point_b['x'] >= 0:  # destination is right of center
        if point_a['x'] >= 0:  # starting point is also right
            # check if distance between point_b - point_a is above threshold
            logger.info(
                "edcm.navigation.compare_coordinates: abs( int(%.2f) - int(%.2f) )" % (point_b['x'], point_a['x']))
            logger.info("edcm.navigation.compare_coordinates: %.2f" % abs(int(point_b['x']) - int(point_a['x'])))
            if abs(int(point_b['x']) - int(point_a['x'])) >= threshold:
                if point_a['x'] < point_b['x']:
                    # starting point_a is left of point_b, go right
                    direction.append("RIGHT")
                    direction.append(int(point_b['x']) - int(point_a['x']))
                else:
                    direction.append("LEFT")
                    direction.append(int(point_a['x']) - int(point_b['x']))
            else:
                direction.append("ON")
                direction.append(int(point_b['x']) - int(point_a['x']))
        else:
            # starting point is left of center, must go right
            distance = abs(int(point_b['x']) + int(point_a['x']))
            if distance > threshold:
                direction.append("RIGHT")
                direction.append(distance)
            else:
                direction.append("ON")
                direction.append(distance)
    else:
        # destination is left of center
        if point_a['x'] <= 0:  # starting_point is also left
            if point_a['x'] <= point_b['x']:
                distance = abs(int(point_a['x']) - int(point_b['x']))
                if distance > threshold:
                    direction.append("RIGHT")
                    direction.append(distance)
                else:
                    direction.append("ON")
                    direction.append(distance)
            else:
                distance = abs(int(point_b['x']) - int(point_a['x']))
                if distance > threshold:
                    direction.append("LEFT")
                    direction.append(distance)
                else:
                    direction.append("ON")
                    direction.append(distance)
        else:
            # starting point is right of center, must go left
            distance = abs(int(point_b['x']) - int(point_a['x']))
            if distance > threshold:
                direction.append("LEFT")
                direction.append(distance)
            else:
                direction.append("ON")
                direction.append(distance)

    # UP/DOWN
    logger.info("point_a[y] = %.f" % point_a['y'])
    logger.info("point_b[y] = %.f" % point_b['y'])
    if point_b['y'] >= 0:  # destination is above of center
        logger.info("edcm.navigation.compare_coordinates: point_b is above center")
        if point_a['y'] >= 0:  # starting point is also above
            logger.info("edcm.navigation.compare_coordinates: point_a is also above center")
            # check if distance between point_b - point_a is above threshold
            logger.info("edcm.navigation.compare_coordinates: abs( int(%.2f) - int(%.2f) )"
                        % (point_b['y'], point_a['y']))
            logger.info("edcm.navigation.compare_coordinates: %.2f" % abs(int(point_b['y']) - int(point_a['y'])))
            distance = abs(int(point_b['y']) - int(point_a['y']))
            if distance > threshold:
                if point_a['y'] < point_b['y']:
                    logger.info("edcm.navigation.compare_coordinates: point_a is below point_b, must go UP")
                    # point_a is below point_b, go UP
                    direction.append("UP")
                    direction.append(distance)
                else:
                    logger.info("edcm.navigation.compare_coordinates: point_a is above point_b, must go DOWN")
                    # starting point_a is above point_b, go DOWN
                    direction.append("DOWN")
                    direction.append(int(point_a['y']) - int(point_b['y']))
            else:
                direction.append('ON')
                direction.append(distance)
        else:
            logger.info("edcm.navigation.compare_coordinates: point_a is below point_b, must go UP")
            # starting point is below center, destination is above, must go UP
            distance = abs(int(point_b['y'])) - int(point_a['y'])
            if distance > threshold:
                direction.append("UP")
                direction.append(distance)
                # vector = "UP %.1f" % distance
            else:
                direction.append("ON")
                direction.append(distance)
    else:
        # destination is below center
        logger.info("edcm.navigation.compare_coordinates: point_b is below center")
        if point_a['y'] <= 0:  # starting_point is also below
            logger.info("edcm.navigation.compare_coordinates: point_a is also below center")
            if point_a['y'] < point_b['y']:
                logger.info("edcm.navigation.compare_coordinates: -point_a is below -point_b, must go UP")
                distance = abs(int(point_a['y']) - int(point_b['y']))
                if distance > threshold:
                    direction.append("UP")
                    direction.append(distance)
                else:
                    direction.append("ON")
                    direction.append(distance)
            else:
                logger.info("edcm.navigation.compare_coordinates: -point_a is above -point_b, must go DOWN")
                distance = abs(int(point_b['y']) - int(point_a['y']))
                if distance > threshold:
                    direction.append("DOWN")
                    direction.append(distance)
                    # vector = "DOWN %.1f" % distance
                else:
                    direction.append("ON")
                    direction.append(distance)
        else:
            # starting point is above center, must go DOWN
            logger.info(
                "edcm.navigation.compare_coordinates: point_a is above center, point_b is below, we must go DOWN")
            distance = abs(int(point_b['y']) - int(point_a['y']))
            if distance > threshold:
                direction.append("DOWN")
                direction.append(distance)
                # vector = "DOWN %.1f" % distance
            else:
                direction.append("ON")
                direction.append(distance)

    logger.info("edcm.navigation.compare_coordinates: direction = %s" % direction)
    logger.info("edcm.navigation.compare_coordinates() completed.")
    return direction


def get_navpoint_offset(testing=False, average=False):
    logger.info("edcm.navigation.get_navpoint_offset(testing=%s, average=%s)" % (testing, average))

    retries = 15
    minimum = 5
    tries = 1
    avg = {'x': 0, 'y': 0}
    total = {'x': 0, 'y': 0}
    while tries <= retries:
        pt = get_navpoint_coordinates()
        if pt is not None:
            total['x'] = pt['x'] + total['x']
            total['y'] = pt['y'] + total['y']
            avg['x'] = total['x'] / tries
            avg['y'] = total['y'] / tries

            if average:
                if tries > minimum:
                    if check_coordinates(avg):
                        logger.info(
                            "edcm.navigation.get_navpoint_offset: return rolling average, navigation_offset = %s" % avg)
                        return avg
            else:
                if check_coordinates(pt):
                    logger.info("edcm.navigation.get_navpoint_offset: return last poll, navigation_offset = %s" % avg)
                    return pt

        tries += 1

        logger.info("tries %d <=> retries %d, tries mod 3 = %.1f" % (tries, retries, tries % 3))
        if (tries % 3) == 0:
            reset()

    logger.info("edcm.navigation.get_navpoint_offset: failure")
    return None


def get_destination_coordinates(testing=False):
    logger.info("edcm.navigation.get_destination_coordinates()")
    coordinates = (0, 0)

    destination_template = cv2.imread(resource_path("..\\templates\\destination.png"), cv2.IMREAD_GRAYSCALE)
    destination_width, destination_height = destination_template.shape[::-1]

    logger.info("edcm.navigation.get_destination_coordinates: screen_size = get_elite_size()")
    screen_size = get_elite_size()

    logger.info("screen_size: left = %s, top = %s, width = %s, height = %s"
                % (screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height']))

    logger.info("edcm.navigation.get_destination_coordinates: screen = get_screen(screen_size=%s)" % screen_size)
    windows.set_elite_active_window()
    screen = get_screen(screen_size)

    logger.info("edcm.navigation.get_destination_coordinates: mask = filter_destination(screen=%s))" % screen)

    mask = filter_destination(screen)
    if testing:
        show_image(mask)

    match = get_image_match(mask, destination_template)

    threshold = .3
    loc = where(match >= threshold)
    for point in zip(*loc[::-1]):
        coordinates = point
        if testing:
            cv2.rectangle(mask, coordinates, (coordinates[0] + destination_width, coordinates[1] + destination_height),
                          (255, 255, 255), 2)

    if testing:
        show_image(mask)

    if coordinates is not None:
        # coordinates are the upper left corner of the matching image.
        # FINAL coordinates include +1/2 the image width and -1/2 the image height
        logger.info("edcm.navigation.get_navpoint_coordinates: "
                    "final_x = (coordinates[x] + ( destination_width * .5 ) ) - ( screen_width * .5 )")
        final_x = (coordinates[0] + (destination_width * .5)) - (screen_size['width'] * .5)
        logger.info("edcm.navigation.get_navpoint_coordinates: "
                    "final_x = ( %.2f + ( %.2f * .5 )) - ( %.2f * .5 ) = %.2f" %
                    (coordinates[0], destination_width, screen_size['width'], final_x))

        logger.info("edcm.navigation.get_navpoint_coordinates: "
                    "final_y = ( screen_height * .5 ) - ( coordinates['y'] + (destination_height * .5 )) ")
        final_y = (screen_size['height'] * .5) - (coordinates[1] + (destination_height * .5))
        logger.info("edcm.navigation.get_navpoint_coordinates: "
                    "final_y = ( %.2f * .5 ) - ( ( %.2f * .5 ) + %.2f ) = %.2f" %
                    (screen_size['height'], destination_height, coordinates[1], final_y))

        return {'x': final_x, 'y': final_y}
    else:
        logger.error("failed to identify coordinates.")
        return None


def get_destination_offset(testing=False, average=False):
    logger.info("edcm.navigation.get_destination_offset(testing=%s,average=%s)" % (testing, average))
    retries = 15
    minimum = 5
    tries = 1
    avg = {'x': 0, 'y': 0}
    total = {'x': 0, 'y': 0}
    while tries <= retries:
        pt = get_destination_coordinates(testing)
        logger.info("edcm.navigation.get_destination_offset: pt = %s" % pt)
        total['x'] = pt['x'] + total['x']
        total['y'] = pt['y'] + total['y']
        avg['x'] = round(total['x'] / tries, 2)
        avg['y'] = round(total['y'] / tries, 2)
        logger.info("edcm.navigation.get_destination_offset: avg = %s" % avg)

        if average:
            if tries > minimum:
                if check_coordinates(avg):
                    logger.info("edcm.navigation.get_destination_offset: return avg, destination_offset = %s" % avg)
                    return avg
        else:
            if check_coordinates(pt):
                logger.info("edcm.navigation.get_destination_offset: return last poll, destination_offset = %s" % avg)
                return pt

        if (tries % 3) == 0:
            logger.info("Tried %i times, resetting position.." % tries)
            reset()

        tries += 1

    logger.info("edcm.navigation.get_destination_offset: failure")
    return None


def x_angle(point=None):
    logger.info("edcm.navigation.x_angle(point=%s)" % str(point))
    if not point:
        return None
    if point['x'] == 0:
        return 0  # avoid div by zero
    result = degrees(atan(point['y'] / point['x']))
    if point['x'] > 0:
        return +90 - result
    else:
        return -90 - result


def navigation_align():
    logger.info("edcm.navigation.navigation_align()")

    center = {'x': 0, 'y': 0}

    ship_status = get_ship_status()['status']

    if not (ship_status == 'in_supercruise' or ship_status == 'in_space'):
        logger.error('align=err1')
        raise Exception('align error 1')

    while sun_percent() > 5:
        send(keymap['PitchUpButton'], state=1)
    send(keymap['PitchUpButton'], state=0)

    logging.info("edcm.navigation.align: set speed for maneuvering")
    send(keymap['SetSpeed50'])

    aligned = False
    x_axis_aligned = False
    x_offset = 0
    pitch_rate = .5
    y_axis_aligned = False
    y_offset = 0
    roll_rate = .25

    while not aligned:

        offset = get_navpoint_offset()
        direction = compare_coordinates(center, offset)

        logger.info("compare_coordinates(center vs offset) ( %s vs %s ) = %s" % (center, offset, direction))

        if direction[0]:
            logger.info("direction[0] == %s" % direction[0])
            if direction[0] != "ON":
                logger.info("x_axis direction = %s" % direction[0])
                if x_offset != 0:
                    logger.info("previous heading = %.f" % x_offset)
                if str(direction[0]).startswith("LEFT"):
                    logger.info("Rotate Left")
                    last_offset = x_offset
                    try:
                        x_offset = float(str(direction[1]))
                    except ValueError:
                        logger.error("compare_coordinates.direction did not parse (%s vs %s) = %s" % (
                            center, direction[2], direction[3]))
                    if x_offset >= last_offset:
                        send(keymap['RollLeftButton'], hold=roll_rate)
                elif str(direction[0]).startswith("RIGHT"):
                    logger.info("Rotate Right")
                    last_offset = x_offset
                    try:
                        x_offset = float(str(direction[1]))
                    except ValueError:
                        logger.error("compare_coordinates.direction did not parse (%s vs %s) = %s" % (
                            center, direction[2], direction[3]))
                    if x_offset >= last_offset:
                        send(keymap['RollRightButton'], hold=roll_rate)
            else:
                x_axis_aligned = True
                x_offset = 0

        if direction[2]:
            logger.info("direction[1] == %s" % direction[1])
            if direction[1] != "ON":
                logger.info("y_axis direction = %s" % direction[1])
            if y_offset != 0:
                logger.info("previous heading = %.f" % y_offset)
            if str(direction[2]).startswith("UP"):
                logger.info("Pitch Up")
                last_offset = y_offset
                try:
                    y_offset = float(str(direction[3]))
                except ValueError:
                    logger.error("compare_coordinates.direction did not parse (%s vs %s) = %s" % (
                        center, direction[2], direction[3]))
                if y_offset >= last_offset:
                    send(keymap['PitchUpButton'], hold=pitch_rate)
            elif str(direction[2]).startswith("DOWN"):
                logger.info("Pitch Down")
                last_offset = y_offset
                try:
                    y_offset = float(str(direction[3]))
                except ValueError:
                    logger.error("compare_coordinates.direction did not parse (%s vs %s) = %s" % (
                        center, direction[2], direction[3]))
                if y_offset >= last_offset:
                    send(keymap['PitchDownButton'], hold=pitch_rate)
            else:
                y_axis_aligned = True
                y_offset = 0

        if x_axis_aligned and y_axis_aligned:
            aligned = True

        if aligned:
            break

    return True


def destination_align():
    logger.info("edcm.navigation.align()")

    center = {'x': 0, 'y': 0}

    ship_status = get_ship_status()['status']

    if not (ship_status == 'in_supercruise' or ship_status == 'in_space'):
        logger.error('align=err1')
        raise Exception('align error 1')

    while sun_percent() > 5:
        send(keymap['PitchUpButton'], state=1)
    send(keymap['PitchUpButton'], state=0)

    logging.info("edcm.navigation.align: set speed for maneuvering")
    send(keymap['SetSpeed50'])

    aligned = False
    x_axis_aligned = False
    x_offset = 0
    pitch_rate = 0.25
    y_axis_aligned = False
    y_offset = 0
    yaw_rate = 0.25

    while not aligned:

        offset = get_destination_offset()
        direction = compare_coordinates(center, offset, threshold=25)

        logger.info("compare_coordinates(center vs offset) ( %s vs %s ) = %s" % (center, offset, direction))

        if direction[0]:
            logger.info("direction[0] == %s" % direction[0])
            if direction[0] != "ON":
                logger.info("x_axis direction = %s" % direction[0])
                if x_offset != 0:
                    logger.info("previous heading = %.f" % x_offset)
                if str(direction[0]).startswith("LEFT"):
                    logger.info("Yaw Left")
                    last_offset = x_offset
                    try:
                        x_offset = float(str(direction[1]))
                    except ValueError:
                        logger.error("compare_coordinates.direction did not parse (%s vs %s) = %s" % (
                            center, direction[2], direction[3]))
                    if x_offset >= last_offset:
                        send(keymap['YawLeftButton'], hold=yaw_rate)
                elif str(direction[0]).startswith("RIGHT"):
                    logger.info("Rotate Right")
                    last_offset = x_offset
                    try:
                        x_offset = float(str(direction[1]))
                    except ValueError:
                        logger.error("compare_coordinates.direction did not parse (%s vs %s) = %s" % (
                            center, direction[2], direction[3]))
                    if x_offset >= last_offset:
                        send(keymap['YawRightButton'], hold=yaw_rate)
            else:
                x_axis_aligned = True
                x_offset = 0

        if direction[2]:
            logger.info("direction[1] == %s" % direction[1])
            if direction[1] != "ON":
                logger.info("y_axis direction = %s" % direction[1])
            if y_offset != 0:
                logger.info("previous heading = %.f" % y_offset)
            if str(direction[2]).startswith("UP"):
                logger.info("Pitch Up")
                last_offset = y_offset
                try:
                    y_offset = float(str(direction[3]))
                except ValueError:
                    logger.error("compare_coordinates.direction did not parse (%s vs %s) = %s" % (
                        center, direction[2], direction[3]))
                if y_offset >= last_offset:
                    send(keymap['PitchUpButton'], hold=pitch_rate)
            elif str(direction[2]).startswith("DOWN"):
                logger.info("Pitch Down")
                last_offset = y_offset
                try:
                    y_offset = float(str(direction[3]))
                except ValueError:
                    logger.error("compare_coordinates.direction did not parse (%s vs %s) = %s" % (
                        center, direction[2], direction[3]))
                if y_offset >= last_offset:
                    send(keymap['PitchDownButton'], hold=pitch_rate)
            else:
                y_axis_aligned = True
                y_offset = 0

        if x_axis_aligned and y_axis_aligned:
            aligned = True

        if aligned:
            break

    return True


def align():
    logger.info("edcm.navigation.align()")

    center = {'x': 0, 'y': 0}

    ship_status = get_ship_status()['status']

    if not (ship_status == 'in_supercruise' or ship_status == 'in_space'):
        logger.error('align=err1')
        raise Exception('align error 1')

    while sun_percent() > 5:
        send(keymap['PitchUpButton'], state=1)
    send(keymap['PitchUpButton'], state=0)

    logging.info("edcm.navigation.align: SetSpeed100")
    send(keymap['SetSpeed100'])

    logging.info("edcm.navigation.align: move away from main star")
    sleep(10)
    send(keymap['SetSpeed50'])

    compass_image, compass_width, compass_height = get_compass_image()
    if check_reverse(compass_image):
        logger.warning("Matched NavCircle, must turn around")
        reverse_direction()

    close = 3
    close_a = 18
    hold_pitch = 0.350 * SHIP_FACTOR
    hold_roll = 0.170 * SHIP_FACTOR

    if ship_status == 'in_space':
        # adjust hold time for nor normal space
        hold_pitch = hold_pitch * .5
        hold_roll = hold_roll * .5

    logging.info("edcm.navigation.align: compass align")
    offset = get_navpoint_offset()
    direction = compare_coordinates(center, offset, close)
    logger.info("compare_coordinates = %s" % direction)

    logging.info("edcm.navigation.align: navpoint_offset = %s " % offset)
    angle = x_angle(offset)
    logging.info("edcm.navigation.align: x_angle = %s " % angle)

    logger.info("edcm.navigation.align: if offset[x] > close and angle > close_a | %s > %s and %s > %s" % (
        offset['x'], close, angle, close_a))

    logger.info("edcm.navigation.align: or offset[x] < -close and angle < -close_a | %s < -%s and %s < -%s" % (
        offset['x'], close, angle, close_a))

    logger.info("edcm.navigation.align: or offset[y] > close or offset[y] <- close | %s > %s and %s > %s" % (
        offset['x'], close, angle, close_a))

    while (offset['x'] > close and angle > close_a) or \
            (offset['x'] < -close and angle < -close_a) or \
            (offset['y'] > close) or \
            (offset['y'] < -close):

        # Roll Into Position
        logger.info("edcm.navigation.align: roll alignment starting")
        while (offset['x'] > close and angle > close_a) or (offset['x'] < -close and angle < -close_a):
            if offset['x'] > close and angle > close:
                logger.info("offset[X] (%.2f) is not close enough (%.2f)" % (offset['x'], close))
                logger.info("send(RollRight) for %.2f s" % hold_roll)
                send(keymap['RollRightButton'], hold=hold_roll)
            if offset['x'] < -close and angle < -close:
                logger.info("offset[X] (%.2f) is not close enough (%.2f)" % (offset['x'], close))
                logger.info("send(RollRight) for %.2f s" % hold_roll)
                send(keymap['RollLeftButton'], hold=hold_roll)
            if get_ship_status()['status'] == 'starting_hyperspace':
                return
            offset = get_navpoint_offset()
            angle = x_angle(offset)
        logger.info("edcm.navigation.align: roll alignment completed")

        # Pitch Into Position
        logger.info("edcm.navigation.align: pitch alignment starting")
        while ((offset['y'] > close) or (offset['y'] < -close)) or \
                ((offset['y'] > close) or (offset['y'] < -close)):
            if offset['y'] > close:
                logger.info("offset[y] (%.2f) is not close enough (%.2f)" % (offset['y'], close))
                logger.info("send(PitchUpButton) for %.2f s" % hold_pitch)
                send(keymap['PitchUpButton'], hold=hold_pitch)
            if offset['y'] < -close:
                logger.info("offset[y] (%.2f) is not close enough (%.2f)" % (offset['y'], close))
                logger.info("send(PitchDownButton) for %.2f s" % hold_pitch)
                send(keymap['PitchDownButton'], hold=hold_pitch)
            if get_ship_status()['status'] == 'starting_hyperspace':
                return
            offset = get_navpoint_offset()
        logger.info("edcm.navigation.align: pitch alignment completed")

        offset = get_navpoint_offset()
        angle = x_angle(offset)

    sleep(0.5)
    close = 50
    hold_pitch = 0.200 * SHIP_FACTOR
    hold_yaw = 0.400 * SHIP_FACTOR

    logging.info('edcm.navigation.align: destination align')
    while (offset['x'] > close) or (offset['x'] < -close) or (offset['y'] > close) or (offset['y'] < -close):

        if offset['x'] > close:
            send(keymap['YawRightButton'], hold=hold_yaw)
        if offset['x'] < -close:
            send(keymap['YawLeftButton'], hold=hold_yaw)
        if offset['y'] > close:
            send(keymap['PitchUpButton'], hold=hold_pitch)
        if offset['y'] < -close:
            send(keymap['PitchDownButton'], hold=hold_pitch)

        if get_ship_status()['status'] == 'starting_hyperspace':
            return

        offset = get_destination_offset()

    logging.info("edcm.navigation.align: full speed ahead")
    send(keymap['SetSpeed100'])

    logging.info("edcm.navigation.align() Completed.")


def jump():
    logging.info("edcm.navigation.jump()")
    tries = 3
    for i in range(tries):
        logging.info("edcm.navigation.jump: try# %s" % i)
        if not (get_ship_status()['status'] == 'in_supercruise' or get_ship_status()['status'] == 'in_space'):
            logging.error('jump=err1')
            raise Exception('not ready to jump')
        sleep(0.5)
        logging.info("edcm.navigation.jump: start fsd")
        send(keymap['HyperSuperCombination'], hold=1)
        sleep(16)
        if get_ship_status()['status'] != 'starting_hyperspace':
            logging.info("edcm.navigation.jump: misaligned, stop fsd")
            send(keymap['HyperSuperCombination'], hold=1)
            sleep(2)
            align()
        else:
            logging.info("edcm.navigation.jump: jumping")
            while get_ship_status()['status'] != 'in_supercruise':
                sleep(1)
            logging.info("edcm.navigation.jump: SetSpeedZer0")
            send(keymap['SetSpeedZero'])
            logging.info("edcm.navigation.jump() Completed")
            return True
    logging.error("edcm.navigation.jump: error, exceeded %s attempts" % tries)
    raise Exception("edcm.navigation.jump() failure")


def refuel(refuel_threshold=33):
    logging.info("edcm.navigation.refuel(refuel_threshold=%s)" % refuel_threshold)

    if get_ship_status()['status'] != 'in_supercruise':
        logging.error('refuel=err1')
        return False

    if get_ship_status()['fuel_percent'] < refuel_threshold and get_ship_status()['star_class'] in FUEL_STARS:
        logging.info("edcm.navigation.refuel: begin refueling ")
        send(keymap['SetSpeed100'])
        #     while not get_ship_status()['is_scooping']:
        #         sleep(1)
        sleep(4)  # crude but effective, on arrival move toward star for 4 seconds
        logging.info("edcm.navigation.refuel: wait for refuel")
        send(keymap['SetSpeedZero'], repeat=3)  # we don't need to repeat 3x, but we do anyway .. for emphasis
        while not get_ship_status()['fuel_percent'] == 100:
            sleep(1)
        logging.info("edcm.navigation.refuel: fuel_percent == 100")
        return True
    elif get_ship_status()['fuel_percent'] >= refuel_threshold:
        logging.info("edcm.navigation.refuel: not needed")
        return False
    elif get_ship_status()['star_class'] not in FUEL_STARS:
        logging.info("edcm.navigation.refuel: not a refueling star")
        return False
    else:
        return False


def reset():
    logging.info("edcm.navigation.reset()")
    logging.info("edcm.navigation.reset: resetting to safe position")

    logging.info("edcm.navigation.reset: 1) go to safe position")
    position()

    logging.info("edcm.navigation.reset: 2) pith up and rotate to reset")
    send(keymap['SetSpeed100'])
    send(keymap['RollRightButton'], state=1)
    send(keymap['PitchUpButton'], state=1)
    duration = 1 + SHIP_FACTOR
    sleep(duration)
    send(keymap['PitchUpButton'], state=0)
    send(keymap['RollRightButton'], state=0)
    send(keymap['SetSpeed100'])


def position(refueled_multiplier=1):
    logging.info("edcm.navigation.position(refueled_multiplier=%s)" % refueled_multiplier)
    logging.info("edcm.navigation.position: discovery scanner (hold)")
    logging.info("edcm.navigation.position: Pitch Up (hold)")
    send(keymap[get_scanner()], state=1)
    send(keymap['PitchUpButton'], state=1)
    sleep(5)
    logging.info("edcm.navigation.position: SetSpeed100")
    send(keymap['PitchUpButton'], state=0)
    send(keymap['SetSpeed100'])
    logging.info("edcm.navigation.position: PitchUp (release)")
    send(keymap['PitchUpButton'], state=1)
    logging.info("edcm.navigation.position: move to safe position")
    while sun_percent() > 3:
        sleep(.2)
    sleep(5)
    send(keymap['PitchUpButton'], state=0)
    sleep(5 * refueled_multiplier)
    logging.info("edcm.navigation.position: discovery scanner (release)")
    send(keymap[get_scanner()], state=0)
    logging.info("edcm.navigation.position() Completed.")
    return True


def auto_launch():
    logging.info("edcm.navigation.auto_launch()")
    ship_status = get_ship_status()['status']
    logger.info("ship_status = %s" % json.dumps(ship_status))
    if ship_status == 'in_station':
        send(keymap['UI_Down'], repeat=2)  # UI move down to AUTO LAUNCH
        send(keymap['UI_Select'])
        logger.info("edcm.navigation.auto_launch: AUTO LAUNCH in progress")
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
                logger.info("t- %.2f, ship_status = %s" % ((t1 - t0), get_ship_status()['status']))
        logger.info("edcm.navigation.auto_launch: AUTO LAUNCH completed in %.2f seconds" % (t1 - t0))
        # boost 3x away
        for i in range(3):
            logger.info("edcm.navigation.auto_launch: boost")
            send(keymap['UseBoostJuice'])
            logger.info("edcm.navigation.auto_launch: power to engines")
            send(keymap['IncreaseEnginesPower'], repeat=3, repeat_delay=.1)
            sleep(7)
            logger.info("edcm.navigation.auto_launch: reset power distribution")
            send(keymap['ResetPowerDistribution'])
    logger.info("edcm.navigation.auto_launch() completed.")


def autopilot():
    logging.info("edcm.navigation.autopilot()")
    logging.info('\n' + 200 * '-' + '\n' + '---- AUTOPILOT START ' + 179 * '-' + '\n' + 200 * '-')
    ship_status = get_ship_status()
    logging.info("edcm.navigation.autopilot: ship_status = %s" % ship_status)
    while ship_status['target']:
        if get_ship_status()['status'] == 'in_space' or get_ship_status()['status'] == 'in_supercruise':
            logging.info('\n' + 200 * '-' + '\n' + '---- navigation_align() ' + 179 * '-' + '\n' + 200 * '-')
            navigation_align()
            logging.info('\n' + 200 * '-' + '\n' + '---- destination_align() ' + 179 * '-' + '\n' + 200 * '-')
            destination_align()
            logging.info('\n' + 200 * '-' + '\n' + '---- jump() ' + 180 * '-' + '\n' + 200 * '-')
            jump()
            logging.info('\n' + 200 * '-' + '\n' + '---- refuel() ' + 178 * '-' + '\n' + 200 * '-')
            refueled = refuel()
            logging.info('\n' + 200 * '-' + '\n' + '---- position() ' + 179 * '-' + '\n' + 200 * '-')
            if refueled:
                position(refueled_multiplier=4)
            else:
                position(refueled_multiplier=1)
        logging.info("edcm.navigation.autopilot: ship_status = %s" % ship_status)
        ship_status = get_ship_status()
    logging.info("edcm.navigation.autopilot: target destination reached")
    send(keymap['SetSpeedZero'])
    logging.info('\n' + 200 * '-' + '\n' + '---- AUTOPILOT END ' + 181 * '-' + '\n' + 200 * '-')


def supercruise():
    logging.info("edcm.navigation.supercruise()")
    ship_status = get_ship_status()
    logging.info("edcm.navigation.autopilot: ship_status = %s" % ship_status)
    while ship_status['status'] == 'in_supercruise':
        navigation_align()
        destination_align()
        ship_status = get_ship_status()
        logging.info("edcm.navigation.autopilot: ship_status = %s" % ship_status)

    return None
