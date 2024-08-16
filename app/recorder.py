# app/recorder.py

import cv2
from datetime import datetime

class Recorder:
    def __init__(self, camera):
        self.camera = camera
        self.out = None
        self.is_recording = False

    def start_recording(self, output_filename):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(output_filename, fourcc, 20.0, (640, 480))
        self.is_recording = True

    def record_frame(self):
        if self.is_recording and self.camera.connected:
            frame = self.camera.get_frame()
            if frame is not None:
                self.out.write(frame)

    def stop_recording(self):
        if self.is_recording:
            self.out.release()
            self.is_recording = False
