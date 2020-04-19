import os
import colorlog
import cv2
import numpy as np
import win32api
import win32con
import win32gui
import win32ui
import ctypes

from edcm import windows

logger = colorlog.getLogger()


def get_screen_size():
    logger.debug("edcm.screen.get_screen_size()")
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    [w, h] = [user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]
    screen_size = {'width': user32.GetSystemMetrics(0),
                   'height': user32.GetSystemMetrics(1),
                   'left': win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN),
                   'top': win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)}
    logger.debug("return: %d, %d, %d, %d" % (
        screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height']))
    return screen_size


def get_elite_size():
    logger.debug("edcm.screen.get_elite_size()")
    screen_size = {}
    elite_hwnd = windows.get_elite_hwnd()
    _left, _top, _right, _bottom = win32gui.GetClientRect(elite_hwnd)
    left, top = win32gui.ClientToScreen(elite_hwnd, (_left, _top))
    right, bottom = win32gui.ClientToScreen(elite_hwnd, (_right, _bottom))
    screen_size['left'] = left
    screen_size['top'] = top
    screen_size['width'] = right - left
    screen_size['height'] = bottom - top
    logger.debug("return get_elite_size: left => %d, top => %d, width => %d, height => %d" % (
        screen_size['left'], screen_size['top'], screen_size['width'], screen_size['height']))
    return screen_size


def get_screen(in_size=None, color="BGR"):
    logger.debug("edcm.screen.get_screen(screen_size=%s)" % in_size)
    screen_size = get_elite_size()
    display_size = get_screen_size()

    logger.debug("%s %s %s %s" % (in_size['top'], in_size['left'], in_size['height'], in_size['width']))

    # if window is full screen
    if display_size['width'] > screen_size['width']:
        # resolution has been scaled
        logger.info("resolution has been scaled: display %s x %s > screen %s x %s"
                    % (display_size['width'], display_size['height'], screen_size['width'], screen_size['height']))

        scalar_x = display_size['width']/screen_size['width']
        scalar_y = display_size['height']/screen_size['height']

        capture = {
            'top': round(int(in_size['top'] * scalar_y)),
            'left': round(int(in_size['left'] * scalar_x)),
            'height': round(int(in_size['height'] * scalar_y)),
            'width': round(int(in_size['width'] * scalar_x))}
        logger.debug("capture[top] = in_size[top] * scalar_x : %s = %s * %s"
                     % (capture['top'], in_size['top'], scalar_x))
        logger.debug("capture[] = in_size[width] * scalar_x : %s = %s * %s"
                     % (capture['width'], in_size['width'], scalar_x))
        logger.debug("capture[width] = in_size[width] * scalar_x : %s = %s * %s"
                     % (capture['width'], in_size['width'], scalar_x))
        logger.debug("capture[width] = in_size[width] * scalar_x : %s = %s * %s"
                     % (capture['width'], in_size['width'], scalar_x))
    else:
        capture = in_size

    logger.debug("%s %s %s %s" % (capture['top'], capture['left'], capture['height'], capture['width']))

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
    memdc.BitBlt((0, 0), (capture['width'], capture['height']), srcdc,
                 (capture['left'], capture['top']), win32con.SRCCOPY)  # copies
    logger.debug(
       "get_screen: memdc.BitBlt((0,0),"
       " (capture['width']= %s, capture['height']= %s, capture['left']= %s, capture['top']= %s),"
       " win32con.SRCCOPY)" % (capture['width'], capture['height'], capture['left'], capture['top']))

    # create Numpy Image Array
    bitmap_data = screenshot.GetBitmapBits(True)
    b_info = screenshot.GetInfo()

    img = np.fromstring(bitmap_data, dtype=np.uint8)
    img.shape = (b_info['bmHeight'], b_info['bmWidth'], 4)

    # clear resources
    srcdc.DeleteDC()
    memdc.DeleteDC()
    win32gui.ReleaseDC(hwin, hwindc)
    win32gui.DeleteObject(screenshot.GetHandle())

    if color.upper() == 'RGB':
        color = cv2.COLOR_BGRA2RGB
    elif color.upper() == 'GRAY':
        color = cv2.COLOR_BGRA2GRAY
    elif color.upper() == 'BGR':
        color = cv2.COLOR_BGRA2BGR

    return cv2.cvtColor(img, color)


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    logger.debug("edcm.screen.resource_path(relative_path=%s)" % relative_path)
    return os.path.abspath(relative_path)


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


def image_filter(image=None, testing=False, equalize_it=False, f1=None, f2=None):
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
    return image_filter(image=image, testing=testing, equalize_it=True, f1=f1, f2=f2)


def filter_sun(image=None, testing=False):
    logger.debug("edcm.screen.filter_sun(image=%s, testing=%s" % (image, testing))
    f1 = [0, 100, 240]
    f2 = [180, 255, 255]
    return image_filter(image=image, testing=testing, equalize_it=True, f1=f1, f2=f2)


def filter_destination(image=None, testing=False):
    logger.debug("edcm.screen.filter_destination(image=%s, testing=%s" % (image, testing))
    # use hsv_slider to attain viewable image containing the destination reticule
    # f1 = [0, 0, 128]  # low pass
    # f2 = [180, 255, 255]  # high pass
    f1 = [15, 15, 220]  # low pass
    f2 = [30, 255, 255]  # high pass
    return image_filter(image=image, testing=testing, equalize_it=False, f1=f1, f2=f2)


def filter_compass(image=None, testing=False):
    logger.debug("edcm.screen.filter_blue(image=%s, testing=%s" % (image, testing))
    f1 = [0, 0, 16]
    f2 = [180, 255, 255]
    return image_filter(image=image, testing=testing, equalize_it=False, f1=f1, f2=f2)


def filter_blue(image=None, testing=False):
    logger.debug("edcm.screen.filter_blue(image=%s, testing=%s" % (image, testing))
    f1 = [0, 100, 200]
    f2 = [180, 100, 255]
    return image_filter(image=image, testing=testing, equalize_it=True, f1=f1, f2=f2)


def hsv_slider(screen_size=None, bandw=False):
    logger.debug("edcm.screen.hsv_slider(screen_size=%s,bandw=%s)" % (screen_size, bandw))
    cv2.namedWindow('image')

    ilow_h = 0
    ihigh_h = 179

    ilow_s = 0
    ihigh_s = 255
    ilow_v = 0
    ihigh_v = 255

    # create trackbars for color change
    cv2.createTrackbar('lowH', 'image', ilow_h, 179, callback)
    cv2.createTrackbar('highH', 'image', ihigh_h, 179, callback)

    cv2.createTrackbar('lowS', 'image', ilow_s, 255, callback)
    cv2.createTrackbar('highS', 'image', ihigh_s, 255, callback)

    cv2.createTrackbar('lowV', 'image', ilow_v, 255, callback)
    cv2.createTrackbar('highV', 'image', ihigh_v, 255, callback)

    while True:
        if screen_size is not None:
            screen_size = get_elite_size()

        # grab the frame
        frame = get_screen(screen_size)

        if bandw:
            frame = equalize(frame)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        # get trackbar positions
        ilow_h = cv2.getTrackbarPos('lowH', 'image')
        ihigh_h = cv2.getTrackbarPos('highH', 'image')
        ilow_s = cv2.getTrackbarPos('lowS', 'image')
        ihigh_s = cv2.getTrackbarPos('highS', 'image')
        ilow_v = cv2.getTrackbarPos('lowV', 'image')
        ihigh_v = cv2.getTrackbarPos('highV', 'image')

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_hsv = np.array([ilow_h, ilow_s, ilow_v])
        higher_hsv = np.array([ihigh_h, ihigh_s, ihigh_v])
        mask = cv2.inRange(hsv, lower_hsv, higher_hsv)

        frame = cv2.bitwise_and(frame, frame, mask=mask)

        # show image
        cv2.imshow('image', frame)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
