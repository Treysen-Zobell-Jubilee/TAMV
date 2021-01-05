
from PIL import ImageTk, Image
from tkinter import ttk
import importlib
import threading
import tkinter
import cv2
import os


class AlgorithmLoader:
    loaded_algorithms = {}

    @staticmethod
    def load_algorithm(name):
        if name in AlgorithmLoader.loaded_algorithms:
            return AlgorithmLoader.loaded_algorithms[name]
        else:
            algorithm = importlib.import_module(f'.{name}', 'tamv_algorithms')
            AlgorithmLoader.loaded_algorithms[name] = algorithm
            return algorithm


class AlgorithmThread(threading.Thread):
    def __init__(self, window):
        self.algorithms = []
        self.window = window

        self.temp_algorithms = []

        self.should_exit = False

        self.frame = None
        self.keypoints = None

        threading.Thread.__init__(self)

    def run(self):
        while not self.should_exit:
            if len(self.temp_algorithms) > 0:
                self.algorithms = self.temp_algorithms.copy()
                self.temp_algorithms.clear()

            frame = self.window.stream.get_frame()
            if frame is not None:
                additional_info = None
                for algorithm in self.algorithms:
                    try:
                        frame, additional_info = algorithm.process(frame, additional_info)
                    except cv2.error:
                        pass
                self.keypoints = additional_info['keypoints']
                self.frame = frame

    def load_algorithms(self, algorithm_names):
        print(algorithm_names)
        self.temp_algorithms = []
        for algorithm_name in algorithm_names:
            algorithm = AlgorithmLoader.load_algorithm(algorithm_name)
            self.temp_algorithms.append(algorithm)

    def close(self):
        self.should_exit = True


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
    def __init__(self, window_title='', video_source=0, desired_fps=60):
        self.window = tkinter.Tk()
        self.window.title(window_title)
        self.window.protocol('WM_DELETE_WINDOW', self.on_close)

        self.__desired_frametime = int((1 / desired_fps) * 1000)

        self.stream = VideoCapture(video_source)
        self.keypoints = None
        self.frame = None

        self.popup = None
        self.algorithms_menu = None

        # Video Stream
        self.stream_canvas = tkinter.Canvas(self.window, width=640, height=480)
        self.stream_canvas.place(x=10, y=10, width=640, height=640)

        # Algorithms Selection
        self.algorithm_selection = tkinter.Listbox(self.window, selectmode=tkinter.SINGLE, width=24, height=16)

        self.algorithm_selection.insert(0, 'gaussian_blur')
        self.algorithm_selection.insert(1, 'grayscale')
        self.algorithm_selection.insert(2, 'hough_circle_finder')
        self.algorithm_selection.place(x=660, y=10, width=150, height=410)

        self.algorithm_selection_move_up = tkinter.Button(self.window, text='Up', width=10, height=5, command=self.move_selection_up)
        self.algorithm_selection_move_up.place(x=660, y=430, width=70, height=20)

        self.algorithm_selection_move_down = tkinter.Button(self.window, text='Down', width=10, height=5, command=self.move_selection_down)
        self.algorithm_selection_move_down.place(x=740, y=430, width=70, height=20)

        self.algorithm_selection_delete = tkinter.Button(self.window, text='Del', width=10, height=5, command=self.delete_selection)
        self.algorithm_selection_delete.place(x=660, y=460, width=70, height=20)

        self.algorithm_selection_add = tkinter.Button(self.window, text='Add', width=10, height=5, command=self.add_selection)
        self.algorithm_selection_add.place(x=740, y=460, width=70, height=20)

        self.algorithm_last_selection = None

        # Algorithm Settings
        self.settings_frame = tkinter.Frame(self.window, relief=tkinter.SUNKEN, borderwidth=2)
        self.settings_canvas = tkinter.Canvas(self.settings_frame)
        self.settings_scrollbar = tkinter.Scrollbar(self.settings_frame, orient='vertical', command=self.settings_canvas.yview)
        self.settings_scrollable_frame = tkinter.Frame(self.settings_canvas)

        self.settings_scrollable_frame.columnconfigure(0, weight=1)
        self.settings_scrollable_frame.columnconfigure(0, weight=5)

        self.settings_scrollable_frame.bind(
            '<Configure>',
            lambda e: self.settings_canvas.configure(
                scrollregion=self.settings_canvas.bbox('all')
            )
        )

        self.settings_canvas.create_window((0, 0), window=self.settings_scrollable_frame, anchor='nw')
        self.settings_canvas.configure(yscrollcommand=self.settings_scrollbar.set)

        self.settings_frame.place(x=11, y=500, width=800, height=150)
        self.settings_canvas.pack(side='left', fill='both', expand=True)
        self.settings_scrollbar.pack(side='right', fill='y')

        self.current_settings = {}

        # Algorithm Thread
        self.algorithm_thread = AlgorithmThread(self)
        self.algorithm_thread.load_algorithms(
            self.algorithm_selection.get(0, self.algorithm_selection.size())
        )
        self.algorithm_thread.start()

        self.overlay = Overlay()

        self.update()
        self.window.mainloop()

    def update(self):
        self.frame = self.algorithm_thread.frame
        self.keypoints = self.algorithm_thread.keypoints

        if self.frame is not None:
            self.frame = ImageTk.PhotoImage(image=Image.fromarray(self.frame))
            self.stream_canvas.create_image(0, 0, image=self.frame, anchor=tkinter.NW)

        try:
            current_algorithm = self.algorithm_selection.get(self.algorithm_selection.curselection())

            algorithm_instance = AlgorithmLoader.loaded_algorithms[current_algorithm]
            try:
                for setting in self.current_settings:
                    algorithm_instance.settings[setting][0] = self.current_settings[setting][2].get()
            except KeyError:
                pass

            if current_algorithm != self.algorithm_last_selection:
                self.algorithm_last_selection = current_algorithm

                self.load_settings(algorithm_instance)

        except tkinter.TclError:
            pass

        self.window.after(self.__desired_frametime, self.update)

    def set_desired_framerate(self, fps):
        self.__desired_frametime = int((1 / fps) * 1000)

    def move_selection_up(self):
        index = self.algorithm_selection.curselection()
        if len(index) < 1:
            index = 0
        else:
            index = index[0]
        selection = self.algorithm_selection.get(index)
        self.algorithm_selection.delete(index)
        self.algorithm_selection.insert(max(index - 1, 0), selection)
        self.algorithm_selection.select_set(max(index - 1, 0))
        self.algorithm_selection.event_generate('<<ListboxSelect>>')

        self.algorithm_thread.load_algorithms(
            self.algorithm_selection.get(0, self.algorithm_selection.size())
        )

    def move_selection_down(self):
        index = self.algorithm_selection.curselection()
        if len(index) < 1:
            index = 0
        else:
            index = index[0]
        selection = self.algorithm_selection.get(index)
        self.algorithm_selection.delete(index)
        print(self.algorithm_selection.size())
        self.algorithm_selection.insert(min(index + 1, self.algorithm_selection.size()), selection)
        self.algorithm_selection.select_set(min(index + 1, self.algorithm_selection.size()))
        self.algorithm_selection.event_generate('<<ListboxSelect>>')

        self.algorithm_thread.load_algorithms(
            self.algorithm_selection.get(0, self.algorithm_selection.size())
        )

    def add_selection(self):
        modules = [f.replace('.py', '') for f in os.listdir('tamv_algorithms') if os.path.isfile(os.path.join('tamv_algorithms', f))]
        modules.remove('__init__')

        self.popup = tkinter.Tk()
        self.popup.wm_title('Add Algorithm')

        self.algorithms_menu = ttk.Combobox(self.popup, values=modules)
        self.algorithms_menu.pack()

        select_button = tkinter.Button(self.popup, text='Select', width=100, height=40, command=self.add_selection_apply)
        select_button.pack()

        self.popup.mainloop()

    def add_selection_apply(self):
        selection = self.algorithms_menu.get()
        self.algorithm_selection.insert(self.algorithm_selection.size(), selection)
        self.algorithm_thread.load_algorithms(
            self.algorithm_selection.get(0, self.algorithm_selection.size())
        )
        self.popup.destroy()

    def delete_selection(self):
        self.algorithm_selection.delete(self.algorithm_selection.curselection())
        self.algorithm_thread.load_algorithms(
            self.algorithm_selection.get(0, self.algorithm_selection.size())
        )

    def on_close(self):
        self.algorithm_thread.should_exit = True
        self.window.destroy()

    def load_settings(self, algorithm):
        for setting in self.current_settings:
            self.current_settings[setting][0].destroy()
            self.current_settings[setting][1].destroy()

        i = 0
        for setting in algorithm.settings:
            value, tkinter_type, minimum_value, maximum_value = algorithm.settings[setting]

            if tkinter_type == 'slider':
                tkinter_label = tkinter.Label(self.settings_scrollable_frame, text=setting)
                tkinter_label.grid(row=i, column=0)

                scale_value = tkinter.IntVar()
                scale_value.set(value)
                tkinter_scale = tkinter.Scale(self.settings_scrollable_frame, from_=minimum_value, to_=maximum_value, orient=tkinter.HORIZONTAL, variable=scale_value, length=400)
                tkinter_scale.grid(row=i, column=1)

                i += 1

                self.current_settings[setting] = (tkinter_label, tkinter_scale, scale_value)

            if tkinter_type == 'checkbox':
                tkinter_label = tkinter.Label(self.settings_scrollable_frame, text=setting)
                tkinter_label.grid(row=i, column=0)

                checkbox_value = tkinter.BooleanVar()
                checkbox_value.set(value)
                tkinter_scale = tkinter.Checkbutton(self.settings_scrollable_frame, var=checkbox_value)
                tkinter_scale.grid(row=i, column=1)

                i += 1

                self.current_settings[setting] = (tkinter_label, tkinter_scale, checkbox_value)


tk_window = Window()
