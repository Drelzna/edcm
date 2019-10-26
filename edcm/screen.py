import sys
from os.path import join, abspath

import colorlog
import cv2
import numpy as np
import win32api
import win32con
import win32gui
import win32ui

from edcm import windows

logger = colorlog.getLogger()


def get_screen_size():
    logger.debug("edcm.screen.get_screen_size()")
    screen_size = {'width': win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN),
                   'height': win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN),
                   'left': win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN),
                   'top': win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)}
    logger.debug("return: %d, %d, %d, %d" % (
        screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height']))
    return screen_size


def get_elite_size():
    logger.debug("edcm.screen.get_elite_size()")
    screen_size = {}
    elite_hwnd = windows.get_elite_hwnd()
    left, top, x2, y2 = win32gui.GetWindowRect(elite_hwnd)
    screen_size['left'] = left
    screen_size['top'] = top
    screen_size['width'] = x2 - left + 1
    screen_size['height'] = y2 - top + 1
    logger.debug("return get_elite_size: left => %d, top => %d, width => %d, height => %d" % (
        screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height']))
    return screen_size


def get_elite_cockpit_size(screen_size=None):
    logger.debug("edcm.screen.get_elite_cockpit_size(screen_size=%s)" % screen_size)
    if not screen_size:
        screen_size = get_elite_size()

    # reduce to cockpit view, upper 3/4 of screen
    screen_size['height'] = round(int(screen_size['height']) * (3 / 4))
    return screen_size


def get_screen(screen_size=None):
    logger.debug("edcm.screen.get_screen(screen_size=%s)" % screen_size)
    if not screen_size:
        screen_size = get_elite_size()

    # get int handle to main desktop
    hwin = win32gui.GetDesktopWindow()

    # create device contexts
    hwindc = win32gui.GetWindowDC(hwin)

    srcdc = win32ui.CreateDCFromHandle(hwindc)  # create PyCDC Object from int handle

    memdc = srcdc.CreateCompatibleDC()  # create a Memory Device Context from source Device Context

    # create a bitmap screenshot
    screenshot = win32ui.CreateBitmap()  # create bit map object
    screenshot.CreateCompatibleBitmap(srcdc, int(screen_size['width']), int(screen_size['height']))  # create bitmap
    memdc.SelectObject(screenshot)

    # copy screen to memory device context
    memdc.BitBlt((0, 0), (screen_size['width'], screen_size['height']), srcdc,
                 (screen_size['left'], screen_size['top']), win32con.SRCCOPY)  # copies
    # logger.debug(
    #    "get_screen: memdc.BitBlt((0,0),"
    #    " (screen_size['width']= %s, screen_size['height']= %s, screen_size['left']= %s, screen_size['top']= %ssrcdc),"
    #    " win32con.SRCCOPY)" % (screen_size['width'], screen_size['height'], screen_size['left'], screen_size['top']))

    # create Numpy Image Array
    bitmap_data = screenshot.GetBitmapBits(True)
    img = np.fromstring(bitmap_data, dtype='uint8')
    img.shape = (screen_size['height'], screen_size['width'], 4)

    # clear resources
    srcdc.DeleteDC()
    memdc.DeleteDC()
    win32gui.ReleaseDC(hwin, hwindc)
    win32gui.DeleteObject(screenshot.GetHandle())

    cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    logger.debug("edcm.screen.resource_path(relative_path=%s)" % relative_path)
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = abspath(".")

    logger.debug("return %s" % join(base_path, relative_path))
    return join(base_path, relative_path)


def callback(x):
    pass


def show_image(image=None):
    if image is not None:
        while True:
            cv2.imshow('edcm.navigation.show_image()', image)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break


def equalize(image):
    """
    convert the incoming image to grey scale and apply Contrast Limited Adaptive Histogram Equalization
    :param image: incoming screen grab image
    :return: processed image, BGR2GRAY+CLAHE
    """
    logger.debug("edcm.screen.equalize(image=%s)" % image)
    # Load the image in greyscale
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # create a CLAHE object (Arguments are optional).
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_clahe = clahe.apply(img_gray)
    img = img_clahe.copy()
    return img


def filter(image=None, testing=False, equalize_it=False, f1=None, f2=None):
    logger.debug("edcm.screen.filter(image=%s, testing=%s, equalize_it=%s, f1=%s, f2=%s)" % (
        image, testing, equalize_it, f1, f2))

    img = image.copy()

    # converting from BGR to HSV color space
    img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    if equalize_it:
        equalized = equalize(img)
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        equalized = cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)
        if testing:
            show_image(equalized)

    # converting from BGR to HSV color space
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    filtered = cv2.inRange(img, np.array(f1), np.array(f2))

    if testing:
        show_image(filtered)

    return filtered


def filter_bright(image=None, testing=False):
    logger.debug("edcm.screen.filter_bright(image=%s, testing=%s" % (image, testing))
    f1 = [0, 0, 215]
    f2 = [0, 0, 255]
    return filter(image=image, testing=testing, equalize_it=True, f1=f1, f2=f2)


def filter_sun(image=None, testing=False):
    logger.debug("edcm.screen.filter_sun(image=%s, testing=%s" % (image, testing))
    f1 = [0, 100, 240]
    f2 = [180, 255, 255]
    return filter(image=image, testing=testing, equalize_it=True, f1=f1, f2=f2)


def filter_destination(image=None, testing=False):
    logger.debug("edcm.screen.filter_destination(image=%s, testing=%s" % (image, testing))
    # use hsv_slider to attain viewable image containing the destination reticule
    f1 = [0, 0, 128]  # low pass
    f2 = [180, 255, 255]  # high pass
    return filter(image=image, testing=testing, equalize_it=True, f1=f1, f2=f2)


def filter_compass(image=None, testing=False):
    logger.debug("edcm.screen.filter_blue(image=%s, testing=%s" % (image, testing))
    f1 = [0, 0, 16]
    f2 = [180, 255, 255]
    return filter(image=image, testing=testing, equalize_it=False, f1=f1, f2=f2)


def filter_blue(image=None, testing=False):
    logger.debug("edcm.screen.filter_blue(image=%s, testing=%s" % (image, testing))
    f1 = [0, 100, 200]
    f2 = [180, 100, 255]
    return filter(image=image, testing=testing, equalize_it=True, f1=f1, f2=f2)


def hsv_slider(screen_size=None, bandw=False):
    logger.debug("edcm.screen.hsv_slider(screen_size=%s,bandw=%s)" % (screen_size, bandw))
    cv2.namedWindow('image')

    ilowH = 0
    ihighH = 179

    ilowS = 0
    ihighS = 255
    ilowV = 0
    ihighV = 255

    # create trackbars for color change
    cv2.createTrackbar('lowH', 'image', ilowH, 179, callback)
    cv2.createTrackbar('highH', 'image', ihighH, 179, callback)

    cv2.createTrackbar('lowS', 'image', ilowS, 255, callback)
    cv2.createTrackbar('highS', 'image', ihighS, 255, callback)

    cv2.createTrackbar('lowV', 'image', ilowV, 255, callback)
    cv2.createTrackbar('highV', 'image', ihighV, 255, callback)

    while (True):
        if screen_size is not None:
            screen_size = get_elite_size()

        # grab the frame
        frame = get_screen(screen_size)

        if bandw:
            frame = equalize(frame)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        # get trackbar positions
        ilowH = cv2.getTrackbarPos('lowH', 'image')
        ihighH = cv2.getTrackbarPos('highH', 'image')
        ilowS = cv2.getTrackbarPos('lowS', 'image')
        ihighS = cv2.getTrackbarPos('highS', 'image')
        ilowV = cv2.getTrackbarPos('lowV', 'image')
        ihighV = cv2.getTrackbarPos('highV', 'image')

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_hsv = np.array([ilowH, ilowS, ilowV])
        higher_hsv = np.array([ihighH, ihighS, ihighV])
        mask = cv2.inRange(hsv, lower_hsv, higher_hsv)

        frame = cv2.bitwise_and(frame, frame, mask=mask)

        # show thresholded image
        cv2.imshow('image', frame)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
