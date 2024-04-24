import cv2
import mediapipe as mp
import numpy as np
import time
import os
import Jackknife as jk
from pathlib import Path
import threading
import collections as col
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import cv2
from PIL import Image, ImageTk
import builtins

X = 0
Y = 1

LIVE_BOOT_TIME = 0
PRE_RECORDED_BOOT_TIME = 1

NUM_POINTS = 21
DIMS = 2
NUM_POINTS_AND_DIMS = NUM_POINTS * DIMS

DEFAULT_TIMES = 'times.npy'

CAN_ERTIS_CODE = True #Update to False to run


HAND_REF = [
    'wrist',
    'thumb_cmc', 'thumb_mcp', 'thumb_ip', 'thumb_tip',
    'index_finger_mcp', 'index_finger_pip', 'index_finger_dip', 'index_finger_tip',
    'middle_finger_mcp', 'middle_finger_pip', 'middle_finger_dip', 'middle_finger_tip',
    'ring_finger_mcp', 'ring_finger_pip', 'ring_finger_dip', 'ring_finger_tip',
    'pinky_mcp', 'pinky_pip', 'pinky_dip', 'pinky_tip',
]

def get_expected_time(time):
    times = np.load(DEFAULT_TIMES)
    return times[time]


def capture_vid(video_name=1):
    spot = PRE_RECORDED_BOOT_TIME

    if isinstance(video_name, int):
        spot = LIVE_BOOT_TIME

    times = np.load(DEFAULT_TIMES)
    expected_boot_time = times[spot]

    print("Initializing Hand Detector")
    actual_boot_time = time.time()
    cap = cv2.VideoCapture(video_name)
    if not cap.isOpened():
        print("Error: Failed to open File.")
        exit()
    actual_boot_time = time.time() - actual_boot_time
    print("HandDetector initialized successfully.")

    times[spot] = expected_boot_time + actual_boot_time / 2
    np.save(DEFAULT_TIMES,times)

    return (cap, mp.solutions.hands.Hands())

def landmarks_to_frame(results):
    if results.multi_hand_landmarks:
        landmarks = [results.multi_hand_landmarks[0]]
        if landmarks:
            for handLms in landmarks:
                # Convert landmarks to dataframe
                points = handLms.landmark
                frame = np.zeros((NUM_POINTS, DIMS))
                for ii, lm in enumerate(points):
                    frame[ii][X] = lm.x
                    frame[ii][Y] = lm.y
        return frame 
    
class Settings:
    def __init__(self):
        #cv2 settings
        self.cv2_resize = (640, 480)
        
        #Frame Buffer Settings
        self.buffer_window = 2
        self.buffer_fps = 15

        self.buffer_frames = self.buffer_window * self.buffer_fps
        self.buffer_length = self.buffer_frames

        #Results Buffer Settings
        self.results_window = 2
        self.results_rps = self.buffer_fps

        self.results_length = self.results_window * self.results_rps

        #templates
        self.home_folder = str(Path(__file__).resolve().parent.parent) + '\\'

        self.raw_template_vids = self.home_folder + 'templatevids\\'
        self.raw_test_vids = self.home_folder + 'testvideos\\'
        
        self.template_data_folder = self.home_folder + 'templates\\'
        self.test_data_folder = self.home_folder + 'tests\\'

        #boot time
        self.boot_time = 5
        
        def recalculate():
            self.buffer_frames = self.buffer_window * self.buffer_fps
            self.buffer_length = self.buffer_frames * NUM_POINTS

class DataHandler:
    def __init__(self, settings=Settings()):
        self.settings = settings

        self.mp4 = None
        self.template = None

        self.templates = None
        self.recognizer = None

        self.classification = None
        self.recognizer = None

        self.frame_buffer = col.deque()
        self.results_buffer = col.deque()

        self.current_result = "Filling Buffer"

        self.capture, self.hands = capture_vid(0)

        self.train_jackknife()

    def update_results(self, results):
        self.results_buffer.append(results)
        best = self.current_result
        if len(self.results_buffer) == self.settings.results_length:
            self.results_buffer.popleft()

            min = self.results_buffer[0][0]
            for result in self.results_buffer:
                if result[0] != -1 and result[0] < min:
                    min = result[0]
                    best = result[1]

            self.current_result = best

    def clear_results(self):
        self.current_result = "Filling Buffer"
        self.frame_buffer = col.deque()
        self.results_buffer = col.deque()


    def terminate_cv2(self):
        self.capture.release()
        cv2.destroyAllWindows()        

    def update_templates(self):
        self.templates = []
        folder = self.settings.template_data_folder
        for path in os.listdir(folder):
            name = path.split('.')[0]
            self.templates.append((name, np.load(folder + '/' + path)))
        
    def train_jackknife(self):
        self.update_templates()
        self.recognizer = jk.Jackknife(templates=self.templates)

    def process_video(self, video_name):
        cap, hands = capture_vid(video_name)

        data = []
        success, img = cap.read()

        while success:
            if not success:
                print("Error in reading!")
                cap.release()
                exit()

            # Image resizing for standardiztion
            img = cv2.resize(img, self.settings.cv2_resize)

            # Running recognition
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = hands.process(imgRGB)

            # Extracting Landmarks
            if results.multi_hand_landmarks:
                frame = landmarks_to_frame(results)
                data.append(frame)

            success, img = cap.read()

        cap.release()
        cv2.destroyAllWindows()

        return data
    
    def save_as_template(self, data="", location = None, name=""):
        if location == -1:
            location = self.settings.template_data_folder
        #Data can be an mp4 path string or a numpy array
        if isinstance(data, str):
            data = self.process_video(data)
            name = data.split('.')[0]
        elif name == "":
            print("Naming error, please include name when saving numpy array")

        np.save(location + "\\" + name, data)
        print("Successfully saved: " + name)
        print("to " + location + "\\" + name + ".npy")

    def save_as_test(self, data="", location = -1, name=""):
        if location == -1:
            location = self.settings.test_data_folder
        # Data:
        # String or numpy template
        if isinstance(data, str):
            data = self.process_video(data)
            name = data.split('.')[0]
        elif name == "":
            print("Naming error, please include name when saving numpy array")

        np.save(location + "\\" + name, data)
        print("Successfully saved: " + name)
        print("to " + location + "\\" + name + ".npy")

    def live_process(self, results):
        clear_console()
        frame = landmarks_to_frame(results)
        self.frame_buffer.append(frame)
        
        print(str(len(self.frame_buffer)) + '/' + str(self.settings.buffer_length))
        if len(self.frame_buffer) == self.settings.buffer_length:
            self.frame_buffer.popleft()
            trajectory = np.array(self.frame_buffer.copy())

            def run():

                original_print = builtins.print
                builtins.print = append_to_console 
                try:
                    self.update_results(d.classify(trajectory))
                finally:
                    builtins.print = original_print
            threading.Thread(target=run).start()


    def frame_process(self):
        cap, hands = capture_vid()
        data = col.deque()
        success, img = cap.read()

        while success:
            if not success:
                print("Error in reading!")
                cap.release()
                exit()

            img = cv2.resize(img, self.settings.cv2_resize)

            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = hands.process(imgRGB)

            if results.multi_hand_landmarks:
                frame = landmarks_to_frame(results)
                data.append(frame)
            
            if len(data) ==  - 1:
                data.popleft()
                trajectory = np.array(data.copy())
                t1 = threading.Thread(target = self.recognizer.classify, args = ((trajectory),))
                print(t1.start())
                
            success, img = cap.read()

        cap.release()
        cv2.destroyAllWindows()
    
    def classify(self, data):
        if isinstance(data, str):
            extension = data.split('.')[1]
            if extension == 'mp4':
                data = self.settings.raw_test_vids + data
                data = self.process_video(data)
                
            else:
                data = self.settings.test_data_folder + data
                data = np.load(data)           

        return self.recognizer.classify(data)

d = DataHandler()
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)


def append_to_console(message):
    def do_append():
        console_output.configure(state='normal')
        console_output.insert(tk.END, message + '\n')
        console_output.configure(state='disabled')
        console_output.see(tk.END)
    main.after(0, do_append)

def clear_console():
    console_output.configure(state='normal')
    console_output.delete('1.0', tk.END)
    console_output.configure(state='disabled')


def update_frame():
    ret, cv_image = d.capture.read()
    current_result.set(d.current_result)
    if ret:
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        results = hands.process(cv_image)
                
        if results.multi_hand_landmarks:            
            d.live_process(results)
            for hand_landmarks in results.multi_hand_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    cv_image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        pil_image = Image.fromarray(cv_image)
        tk_image = ImageTk.PhotoImage(image=pil_image)
        canvas.itemconfig(image_on_canvas, image=tk_image)
        canvas.image = tk_image

    main.after(10, update_frame)


def run_button_clicked():
    file_path = runP.get()
    if file_path:
        def run():
            clear_console()
            original_print = builtins.print
            builtins.print = append_to_console 
            try:
                d.classify(file_path)
            finally:
                builtins.print = original_print
        threading.Thread(target=run).start()
    else:
        append_to_console("Please enter a file name or path.")
  
def record_video():
    vid_name = recordP.get() + ".mp4"
    directory = d.settings.raw_template_vids
    video_path = os.path.join(directory, vid_name)

    fourcc = cv2.VideoWriter_fourcc(*'h264')
    out = cv2.VideoWriter(video_path, fourcc, 20, (640, 480))

    start_time = time.time()
    while int(time.time() - start_time) < 4:
        ret, frame = d.capture.read()
        if ret:
            out.write(frame)
        else:
            break

    out.release()
    print("Finished recording")

def start_recording():
    threading.Thread(target=record_video).start()

if not CAN_ERTIS_CODE:
    main = tk.Tk()
    main.title('ASCL Prototype')
    main.geometry('600x900')

    title_label = ttk.Label(main, text='ASCL', font='Calibri 24 bold')
    title_label.pack(pady=10)

    update_label = ttk.Label(main, text='MP4 Recording works too', font='Calibri 12')
    update_label.pack(pady=10)

    canvas = tk.Canvas(main, width=400, height=400)
    canvas.pack(side=tk.TOP, padx=20, pady=10)
    image_on_canvas = canvas.create_image(200, 200, anchor='center')

    record_frame = ttk.Frame(main)
    record_frame.pack(side=tk.TOP, fill=tk.X, pady=(10, 0))

    record_button = ttk.Button(record_frame, text='Record', command=start_recording)
    record_button.pack(side=tk.RIGHT, padx=10)

    recordP = ttk.Entry(record_frame)
    recordP.pack(side=tk.RIGHT, padx=10)

    run_frame = ttk.Frame(main)
    run_frame.pack(side=tk.TOP, fill=tk.X, pady=(10, 0))

    run_button = ttk.Button(run_frame, text='Run', command=run_button_clicked)
    run_button.pack(side=tk.RIGHT, padx=10)

    runP = ttk.Entry(run_frame)
    runP.pack(side=tk.RIGHT, padx=10)

    live_frame = ttk.Frame(main)
    live_frame.pack(side=tk.TOP, fill=tk.X, pady=(10, 0))

    #live_button = ttk.Button(live_frame, text='Live', command=d.live_process)
    #live_button.pack(side=tk.RIGHT, padx=10)

    #This clears both buffers
    clear_button = ttk.Button(live_frame, text='Clear', command=d.clear_results)
    clear_button.pack(side=tk.RIGHT, padx=10)

    #The results buffer has been added where live button used to be
    #Lines 95 and 96 control the length
    current_result = tk.StringVar()
    result_label = ttk.Label(live_frame, background='white', textvariable=current_result)
    result_label.pack(side=tk.RIGHT, padx=10)

    console_output = scrolledtext.ScrolledText(main, height=16)
    console_output.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 20))


    update_frame()

    main.mainloop()

    d.terminate_cv2()
else:
    print()
    print('~~~~~~~~~~~~')
    print('Check line 29')
    print('~~~~~~~~~~~~')
    print()








    










