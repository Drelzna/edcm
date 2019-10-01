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
    logger.info("get_screen_size()")
    screen_size = {}
    screen_size['width'] = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    screen_size['height'] = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    screen_size['left'] = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    screen_size['top'] = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
    logger.debug("return: %d, %d, %d, %d" % (
        screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height']))
    return screen_size


def get_elite_size():
    logger.info("get_elite_size()")
    screen_size = {}
    elite_hwnd = windows.get_elite_hwnd()
    x, y, w, h = win32gui.GetWindowRect(elite_hwnd)
    screen_size['left'] = x
    screen_size['top'] = y
    screen_size['width'] = w - x
    screen_size['height'] = h - y
    logger.debug("return get_elite_size: left => %d, top => %d, width => %d, height => %d" % (
        screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height']))
    return screen_size


def get_elite_cockpit_size(screen_size=None):
    if not screen_size:
        screen_size = get_elite_size()

    # reduce to cockpit view
    screen_size['left'] = round(int(screen_size['width']) * (1 / 3))
    screen_size['top'] = round(int(screen_size['height']) * (1 / 3))
    screen_size['width'] = round(int(screen_size['width']) * (2 / 3))
    screen_size['height'] = round(int(screen_size['height']) * (2 / 3))
    return screen_size


def get_screen(screen_size=None):
    # logger.info("get_screen(screen_size=%s)" % screen_size)
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
    logger.info("resource_path(%s)" % relative_path)
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = abspath(".")

    logger.debug("return %s" % join(base_path, relative_path))
    return join(base_path, relative_path)


def callback(x):
    pass


def equalize(image):
    """
    convert the incoming image to grey scale and apply Contrast Limited Adaptive Histogram Equalization
    :param image: incoming screen grab image
    :return: processed image, BGR2GRAY+CLAHE
    """
    img = image.copy()
    # Load the image in greyscale
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # create a CLAHE object (Arguments are optional).
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_clahe = clahe.apply(img_gray)
    return img_clahe


def filter(image=None, testing=False, equalize_it=False, f1=None, f2=None):
    while True:
        screen_size = get_elite_size()

        if testing:
            img = get_screen(screen_size)
        else:
            img = image.copy()

        if equalize_it:
            equalized = equalize(img)
            equalized = cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)
            img = cv2.cvtColor(equalized, cv2.COLOR_BGR2HSV)

        filtered = cv2.inRange(img, np.array(f1), np.array(f2))

        if testing:
            cv2.imshow('Filtered', filtered)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
        else:
            break

    return filtered


def filter_bright(image=None, testing=False):
    f1 = [0, 0, 215]
    f2 = [0, 0, 255]
    return filter(image=image, testing=testing, equalize_it=True, f1=f1, f2=f2)


def filter_sun(image=None, testing=False):
    f1 = [0, 100, 240]
    f2 = [180, 255, 255]
    return filter(image=image, testing=testing, equalize_it=True, f1=f1, f2=f2)


def filter_orange(image=None, testing=False):
    f1 = [15, 220, 220]
    f2 = [30, 255, 255]
    return filter(image=image, testing=testing, equalize_it=True, f1=f1, f2=f2)


def filter_blue(image=None, testing=False):
    f1 = [0, 0, 200]
    f2 = [180, 100, 255]
    return filter(image=image, testing=testing, equalize_it=True, f1=f1, f2=f2)


def hsv_slider(bandw=False):
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
        screen_size = get_elite_size()

        # grab the frame
        frame_x1 = screen_size['width'] * 5 / 16
        frame_y1 = screen_size['height'] * 5 / 8
        frame_x2 = screen_size['width'] * 2 / 4
        frame_y2 = screen_size['height'] * 15 / 16
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
