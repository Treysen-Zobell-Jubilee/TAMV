
import numpy as np
import cv2


settings = {}


def process(frame, args):
    circles = cv2.HoughCircles(frame, cv2.HOUGH_GRADIENT, 1.2, 100)
    keypoints = []
    if circles is not None:
        circles = np.round(circles[0, :]).astype('int')
        for (x, y, r) in circles:
            keypoints.append((x, y))
    return frame, {'keypoints': keypoints}
