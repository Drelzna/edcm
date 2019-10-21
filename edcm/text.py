##Loading the necessary packages
import numpy as np
import cv2
from imutils.object_detection import non_max_suppression
import pytesseract
from matplotlib import pyplot as plt

# Creating argument dictionary for the default arguments needed in the code.
args = {"image": "../test/images/Screenshot_00001.bmp",
        "east": "../lib/text/frozen_east_text_detection.pb",
        "min_confidence": 0.5, "width": 1920, "height": 1080}


