import logging
import os
import importlib.util
import cv2
import sys
from PyQt5.QtWidgets import QMainWindow
from flask import Flask, Response, jsonify, request
from app.camera import Camera
from app.recorder import Recorder
from app.detector import MotionDetector
from app.face_detector import FaceDetector
from app.explosion_detection import ExplosionDetector
from app.person_detector import PersonDetector
from app.vehicle_detector import VehicleDetector
from app.animal_detector import AnimalDetector
from PyQt5.QtCore import QTimer
from datetime import datetime

app = Flask(__name__)
main_window = None

class MainWindow(QMainWindow):
    def __init__(self, camera_id):
        global main_window
        super(MainWindow, self).__init__()
        main_window = self

        self.camera_index_map = {}
        self.frame_counts = []
        self.fps_start_times = []
        self.fps_values = []

        self.cameras = []
        self.recorders = []
        self.detectors = []
        self.motion_detected = []
        self.thresholds = {}
        self.enable_face_detection = {}
        self.enable_person_detection = {}
        self.enable_vehicle_detection = {}
        self.enable_animal_detection = {}
        self.enable_explosion_detection = {}  # Add explosion detection setting
        self.main_display_camera_id = None
        self.main_display_needs_update = False

        self.settings_dir = "/home/risc3/new_nvring/NVRR/nvr1_project/configs/NVR_camsettings"
        self.available_camera_indices = [camera_id]
        self.load_settings()

        # Find the maximum camera ID to initialize lists correctly
        max_camera_id = max(self.available_camera_indices)
        self.explosion_detectors = [None] * (max_camera_id + 1)
        self.face_detectors = [None] * (max_camera_id + 1)
        self.cameras = [None] * (max_camera_id + 1)
        self.recorders = [None] * (max_camera_id + 1)
        self.detectors = [None] * (max_camera_id + 1)
        self.motion_detected = [False] * (max_camera_id + 1)
        self.frame_counts = [0] * (max_camera_id + 1)
        self.fps_start_times = [datetime.now()] * (max_camera_id + 1)
        self.fps_values = [0] * (max_camera_id + 1)

        self.person_detector = PersonDetector()
        self.vehicle_detector = VehicleDetector()
        self.animal_detector = AnimalDetector()

        self.init_ui()

        for settings in self.camera_settings:
            camera_id = settings['camera_id']
            logging.debug(f"Initializing face detector for camera {camera_id}")
            self.face_detectors[camera_id] = FaceDetector()

            logging.debug(f"Initializing explosion detector for camera {camera_id}")
            self.explosion_detectors[camera_id] = ExplosionDetector()

            try:
                camera = Camera(camera_id)
                if not camera.connected:
                    logging.error(f"Camera with ID {camera_id} cannot be opened.")
                    continue  # Skip this camera and move to the next one
                self.cameras[camera_id] = camera
                self.camera_index_map[camera_id] = camera
                recorder = Recorder(camera)
                threshold = settings['threshold']
                self.thresholds[camera_id] = threshold
                detector = MotionDetector(threshold)
                self.recorders[camera_id] = recorder
                self.detectors[camera_id] = detector
                self.motion_detected[camera_id] = False
                recorder.start_recording(f'output_{camera_id}.avi')
                self.enable_face_detection[camera_id] = settings.get('enable_face_detection', False)
                self.enable_person_detection[camera_id] = settings.get('enable_person_detection', False)
                self.enable_vehicle_detection[camera_id] = settings.get('enable_vehicle_detection', False)
                self.enable_animal_detection[camera_id] = settings.get('enable_animal_detection', False)
                self.enable_explosion_detection[camera_id] = settings.get('enable_explosion_detection', False)  # Add explosion detection setting
            except Exception as e:
                logging.error(f"Error initializing camera {camera_id}: {e}")

        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self.update_frames)
        self.frame_timer.start(30)

        self.report_timer = QTimer(self)
        self.report_timer.timeout.connect(self.report_motion)
        self.report_timer.start(1000)

    def load_settings(self):
        self.camera_settings = []
        for i in self.available_camera_indices:
            settings_path = os.path.join(self.settings_dir, f'camera_{i}.py')
            settings = self.load_camera_settings(settings_path, i)
            self.camera_settings.append(settings)

    def load_camera_settings(self, filepath, default_id):
        settings = {
            "camera_id": default_id,
            "threshold": 1000,
            "enable_face_detection": False,
            "enable_person_detection": False,
            "enable_vehicle_detection": False,
            "enable_animal_detection": False,
            "enable_explosion_detection": False  # Add explosion detection setting
        }
        if os.path.exists(filepath):
            spec = importlib.util.spec_from_file_location("settings", filepath)
            settings_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings_module)
            settings["camera_id"] = getattr(settings_module, "camera_id", default_id)
            settings["threshold"] = getattr(settings_module, "threshold", 1000)
            settings["enable_face_detection"] = getattr(settings_module, "enable_face_detection", False)
            settings["enable_person_detection"] = getattr(settings_module, "enable_person_detection", False)
            settings["enable_vehicle_detection"] = getattr(settings_module, "enable_vehicle_detection", False)
            settings["enable_animal_detection"] = getattr(settings_module, "enable_animal_detection", False)
            settings["enable_explosion_detection"] = getattr(settings_module, "enable_explosion_detection", False)  # Add explosion detection setting
        return settings

    def save_camera_settings(self, filepath, camera_id, threshold, enable_face_detection, enable_person_detection, enable_vehicle_detection, enable_animal_detection, enable_explosion_detection):
        with open(filepath, 'w') as f:
            f.write(f"camera_id = {camera_id}\n")
            f.write(f"threshold = {threshold}\n")
            f.write(f"enable_face_detection = {enable_face_detection}\n")
            f.write(f"enable_person_detection = {enable_person_detection}\n")
            f.write(f"enable_vehicle_detection = {enable_vehicle_detection}\n")
            f.write(f"enable_animal_detection = {enable_animal_detection}\n")
            f.write(f"enable_explosion_detection = {enable_explosion_detection}\n")  # Add explosion detection setting

    def init_ui(self):
        self.setGeometry(0, 0, 1, 1)
        self.setWindowTitle('NVR Application')

    def update_frames(self):
        current_time = datetime.now()
        for i, camera in enumerate(self.cameras):
            if camera is None or not camera.connected:
                continue  # Skip if the camera is not initialized or not connected
            frame = camera.get_frame()
            if frame is not None:
                self.frame_counts[i] += 1
                elapsed_time = (current_time - self.fps_start_times[i]).total_seconds()
                if elapsed_time >= 1.0:
                    self.fps_values[i] = self.frame_counts[i] / elapsed_time
                    self.frame_counts[i] = 0
                    self.fps_start_times[i] = current_time

                self.motion_detected[i] = self.detectors[i].detect(frame)
                if self.motion_detected[i]:
                    self.main_display_camera_id = i
                    self.main_display_needs_update = True

                if self.main_display_camera_id == i:
                    if self.enable_face_detection[camera.camera_id]:
                        frame = self.face_detectors[i].detect_and_draw(frame)
                    if self.enable_person_detection[camera.camera_id]:
                        frame = self.person_detector.detect_and_draw(frame)
                    if self.enable_vehicle_detection[camera.camera_id]:
                        frame = self.vehicle_detector.detect_and_draw(frame)
                    if self.enable_animal_detection[camera.camera_id]:
                        frame = self.animal_detector.detect_and_draw(frame)
                    if self.enable_explosion_detection[camera.camera_id]:
                        frame = self.explosion_detectors[i].detect_and_draw(frame)

                self.recorders[i].record_frame()

    def report_motion(self):
        messages = []
        for i, detected in enumerate(self.motion_detected):
            if detected:
                messages.append(f"Object detected in cam {self.cameras[i].camera_id}")
        if messages:
            print("\n".join(messages))
        else:
            print("No motion detected")

    def refresh_feeds(self):
        for i, camera in enumerate(self.cameras):
            if camera is None or not camera.connected:
                continue  # Skip if the camera is not initialized or not connected
            frame = camera.get_frame()
            if frame is not None:
                if self.enable_face_detection[camera.camera_id]:
                    frame = self.face_detectors[i].detect_and_draw(frame)
                if self.enable_person_detection[camera.camera_id]:
                    frame = self.person_detector.detect_and_draw(frame)
                if self.enable_vehicle_detection[camera.camera_id]:
                    frame = self.vehicle_detector.detect_and_draw(frame)
                if self.enable_animal_detection[camera.camera_id]:
                    frame = self.animal_detector.detect_and_draw(frame)
                if self.enable_explosion_detection[camera.camera_id]:
                    frame = self.explosion_detectors[i].detect_and_draw(frame)
                print(f"Refreshed feed for Camera {camera.camera_id}")

@app.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    return Response(gen_frames(camera_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/cameras', methods=['GET'])
def list_cameras():
    global main_window
    return jsonify(list(main_window.camera_index_map.keys()))

@app.route('/motion_status', methods=['GET'])
def motion_status():
    try:
        status = {camera_id: detection_status for camera_id, detection_status in main_window.detection_status.items()}
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

logging.basicConfig(level=logging.INFO)

def gen_frames(camera_id):
    global main_window
    while True:
        try:
            camera = main_window.camera_index_map.get(camera_id)
            if camera is None or not camera.connected:
                logging.error(f"Camera {camera_id} is not connected or initialized.")
                continue

            frame = camera.get_frame()
            if frame is None:
                logging.error(f"No frame received from camera {camera_id}.")
                continue

            display_frame = frame.copy()

            if main_window.enable_face_detection.get(camera_id, False):
                logging.debug(f"Face detection enabled for camera {camera_id}.")
                display_frame = main_window.face_detectors[camera_id].detect_and_draw(display_frame)

            if main_window.enable_person_detection.get(camera_id, False):
                logging.debug(f"Person detection enabled for camera {camera_id}.")
                display_frame = main_window.person_detector.detect_and_draw(display_frame)

            if main_window.enable_vehicle_detection.get(camera_id, False):
                logging.debug(f"Vehicle detection enabled for camera {camera_id}.")
                display_frame = main_window.vehicle_detector.detect_and_draw(display_frame)

            if main_window.enable_animal_detection.get(camera_id, False):
                logging.debug(f"Animal detection enabled for camera {camera_id}.")
                display_frame = main_window.animal_detector.detect_and_draw(display_frame)

            if main_window.enable_explosion_detection.get(camera_id, False):
                logging.debug(f"Explosion detection enabled for camera {camera_id}.")
                display_frame = main_window.explosion_detectors[camera_id].detect_and_draw(display_frame)

            logging.debug(f"Encoding frame to JPEG for camera {camera_id}.")
            ret, buffer = cv2.imencode('.jpg', display_frame)
            if not ret:
                logging.error(f"Failed to encode frame to JPEG for camera {camera_id}.")
                continue

            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            logging.error(f"Error in gen_frames for camera {camera_id}: {e}")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + b'Error in gen_frames' + b'\r\n')
