
import cv2


settings = {
    'blur_x': [1, 'slider', 1, 35],  # value, type, low end, high end
    'blur_y': [1, 'slider', 1, 35],
    'use_blur': [True, 'checkbox', False, True],
    'null_field0': [1, 'slider', 1, 35],  # value, type, low end, high end
    'null_field1': [1, 'slider', 1, 35]
}


def make_odd(val):
    if not val % 2:
        val += 1

    return int(val)


def process(frame, args):
    blur_x = make_odd(settings['blur_x'][0])
    blur_y = make_odd(settings['blur_y'][0])

    if not settings['use_blur'][0]:
        blur_x = 1
        blur_y = 1

    return cv2.GaussianBlur(frame, (blur_x, blur_y), 0), {'keypoints': None}
