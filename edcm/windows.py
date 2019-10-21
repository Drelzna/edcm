import logging
import os
from time import sleep

import colorlog
import psutil
import win32gui
import win32process
from win32con import SWP_NOSIZE, SWP_NOMOVE, HWND_TOP

logger = colorlog.getLogger()

logger.setLevel(logging.ERROR)

EXECUTABLE = "EliteDangerous64.exe"
CLASS_NAME = "Elite:Dangerous Executable"
WINDOW_NAME = "Elite - Dangerous (CLIENT)"


def get_hwnd_info(hwnd):
    logger.info("get_hwnd_info(%s)" % hwnd)
    dim = {}
    if hwnd:
        rect = win32gui.GetWindowRect(hwnd)
        if rect:
            dim['x'] = rect[0]
            dim['y'] = rect[1]
            dim['w'] = rect[2] - dim['x']
            dim['h'] = rect[3] - dim['y']
    return dim


def get_dimensions(rect):
    logger.info("get_dimensions(%s)" % rect)


def print_hwnd_info(hwnd):
    if hwnd:
        dim = get_hwnd_info(hwnd)
        logger.info("Window ( %s / %s ):" % (win32gui.GetClassName(hwnd), win32gui.GetWindowText(hwnd)))
        logger.info("Location: (%d, %d)" % (dim['x'], dim['y']))
        logger.info("Size: (%d, %d)" % (dim['w'], dim['h']))


def get_hwnd_by_pid(pid=None):
    logger.info("get_hwnd_by_pid(%s)" % pid)

    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            zzz, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                get_hwnd_info(hwnd)
                hwnds.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds


def get_hwnd(class_name=None, window_name=WINDOW_NAME):
    return win32gui.FindWindow(class_name, window_name)


def get_elite_hwnd():
    logger.info("get_elite_hwnd()")
    for proc in psutil.process_iter():
        if proc.name() == EXECUTABLE:
            pid = proc.pid
            m = get_hwnd_by_pid(pid)
            if len(m) == 1:
                return m[0]
    return False


def get_elite_hwindc():
    logger.info("get_elite_hwindc")
    hwnd = get_elite_hwnd()
    return win32gui.GetWindowDC(hwnd)


def set_elite_active_window(elite_hwnd=None):
    logger.info("set_elite_active_window()")
    if not elite_hwnd:
        elite_hwnd = get_elite_hwnd()
    foreground_window = get_foreground_window()
    if "Task Switching" in foreground_window:
        logger.debug("Task Switching, skip")
        return
    logger.debug("Foreground Window is: %s" % foreground_window)
    if not "Elite - Dangerous" in foreground_window:
        if elite_hwnd:
            set_active_window(elite_hwnd)


def set_active_window(hwnd=None):
    logger.info("set_active_window(%s)" % hwnd)
    if hwnd:
        win32gui.SetForegroundWindow(hwnd)
        win32gui.BringWindowToTop(hwnd)
        win32gui.SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE)
        sleep(0.2)


def get_foreground_window():
    logger.info("get_foreground_window()")
    fgw = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(fgw)


def get_my_hwnd():
    print("get_my_hwnd()")
    # try executing pid
    pid = os.getpid()
    print("my pid = %s" % pid)
    m = get_hwnd_by_pid(pid)
    if len(m) == 1:
        return m[0]
    print("hwnd not found, looking for parent pid")
    p = psutil.Process(pid)
    ppid = p.ppid()
    m = get_hwnd_by_pid(ppid)
    if len(m) == 1:
        return m[0]
    print("hwnd not found")
    return False
