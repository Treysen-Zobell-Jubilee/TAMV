
import cv2


settings = {}


def process(frame, args):
    return cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY), ({'keypoints': None, 'blur': 11})
