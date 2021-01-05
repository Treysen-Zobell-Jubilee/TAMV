"""
Layout:
    Threads:
        Video Stream Display (Main)
        Overlay Generator
        Algorithms
        User Input
"""

from PIL import ImageTk, Image
import tkinter
import cv2
import numpy as np


class Overlay:
    def __init__(self):
        self.overlays = []

    def draw(self, frame):
        for overlay in self.overlays:
            if overlay[0] == 'circle':
                frame = cv2.circle(frame, *tuple(overlay[1:]))

            elif overlay[0] == 'crosshair0':
                frame = cv2.line(frame,
                                 (overlay[1][0] - overlay[2], overlay[1][1]),
                                 (overlay[1][0] + overlay[2], overlay[1][1]),
                                 overlay[3], overlay[4])
                frame = cv2.line(frame,
                                 (overlay[1][0], overlay[1][1] - overlay[2]),
                                 (overlay[1][0], overlay[1][1] + overlay[2]),
                                 overlay[3], overlay[4])

        return frame

    def clear(self):
        self.overlays = []

    def add_circle(self, position, radius, color=(255, 0, 0), stroke=1):
        self.overlays.append(['circle', position, radius, color, stroke])

    def add_crosshair(self, position, radius, color=(255, 0, 0), stroke=1, style=0):
        self.overlays.append([f'crosshair{style}', position, radius, color, stroke])


class VideoCapture:
    def __init__(self, video_source=0):
        self.stream = cv2.VideoCapture(video_source)
        if not self.stream.isOpened():
            raise ValueError('Unable to open video source ', video_source)

        self.width = self.stream.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self):
        if self.stream.isOpened():
            success, frame = self.stream.read()
            if success:
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                return None
        else:
            return None

    def __del__(self):
        if self.stream.isOpened():
            self.stream.release()


class Window:
    def __init__(self, window_title='', video_source=0):
        self.window = tkinter.Tk()
        self.window.title(window_title)

        self.stream = VideoCapture(video_source)
        self.frame = None

        self.canvas = tkinter.Canvas(self.window, width=self.stream.width, height=self.stream.height)
        self.canvas.pack()

        self.overlay = Overlay()
        self.overlay.add_circle((int(self.stream.width / 2), int(self.stream.height / 2)), 10)
        self.overlay.add_crosshair((int(self.stream.width / 2), int(self.stream.height / 2)), 10)

        self.update()
        self.window.mainloop()

    def update(self):
        self.frame = self.stream.get_frame()

        # Search algorithms here
        self.overlay.clear()
        grayscale = cv2.cvtColor(self.frame, cv2.COLOR_RGB2GRAY)
        circles = cv2.HoughCircles(grayscale, cv2.HOUGH_GRADIENT, 1.2, 100)
        if circles is not None:
            circles = np.round(circles[0, :]).astype('int')
            for (x, y, r) in circles:
                self.overlay.add_circle((x, y), r, (0, 255, 0))
        # Done

        self.frame = self.overlay.draw(self.frame)

        if self.frame is not None:
            self.frame = ImageTk.PhotoImage(image=Image.fromarray(self.frame))
            self.canvas.create_image(0, 0, image=self.frame, anchor=tkinter.NW)

        self.window.after(1, self.update)


window = Window()
