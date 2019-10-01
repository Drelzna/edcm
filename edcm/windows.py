import os
import sys
from os.path import abspath, join

import psutil
import colorlog
import win32gui
import win32process

logger = colorlog.getLogger()

EXECUTABLE = "EliteDangerous64.exe"
CLASS_NAME = "Elite:Dangerous Executable"
WINDOW_NAME = "Elite - Dangerous (CLIENT)"


def get_hwnd_info(hwnd):
    logger.info("get_hwnd_info(%s)" % hwnd)
    rect = win32gui.GetWindowRect(hwnd)
    x = rect[0]
    y = rect[1]
    w = rect[2] - x
    h = rect[3] - y
    logger.info("Window ( %s / %s ):" % (win32gui.GetClassName(hwnd), win32gui.GetWindowText(hwnd)))
    logger.info("Location: (%d, %d)" % (x, y))
    logger.info("Size: (%d, %d)" % (w, h))


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
    if elite_hwnd:
        logger.debug("EliteDangerous is running, set to Foreground")
        win32gui.SetForegroundWindow(elite_hwnd)


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