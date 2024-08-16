import sys
import requests
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QScrollArea, QFrame, QGridLayout, QComboBox, QPushButton, QMessageBox, QCheckBox, QDialog
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal, QByteArray
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget

logging.basicConfig(level=logging.DEBUG)

NVR_SERVER_URLS = [
    'http://192.168.6.113:5001',
    'http://192.168.6.113:5002'
]

class MotionStatusThread(QThread):
    motion_status_signal = pyqtSignal(dict)

    def run(self):
        while True:
            for url in NVR_SERVER_URLS:
                try:
                    response = requests.get(f'{url}/motion_status')
                    response.raise_for_status()
                    motion_status = response.json()
                    logging.debug(f"Motion status from {url}: {motion_status}")
                    self.motion_status_signal.emit(motion_status)
                except requests.RequestException as e:
                    logging.error(f"Failed to fetch motion status from {url}: {e}")
                    logging.error(f"Response content: {response.content if response else 'No response content'}")
            self.msleep(5000)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Detection Settings")
        self.setFixedSize(300, 300)
        
        self.layout = QVBoxLayout(self)
        
        self.camera_selector = QComboBox(self)
        self.layout.addWidget(self.camera_selector)

        self.face_checkbox = QCheckBox("Face Detection", self)
        self.face_checkbox.setStyleSheet("color: black;")
        self.layout.addWidget(self.face_checkbox)

        self.person_checkbox = QCheckBox("Person Detection", self)
        self.person_checkbox.setStyleSheet("color: black;")
        self.layout.addWidget(self.person_checkbox)

        self.vehicle_checkbox = QCheckBox("Vehicle Detection", self)
        self.vehicle_checkbox.setStyleSheet("color: black;")
        self.layout.addWidget(self.vehicle_checkbox)

        self.animal_checkbox = QCheckBox("Animal Detection", self)
        self.animal_checkbox.setStyleSheet("color: black;")
        self.layout.addWidget(self.animal_checkbox)

        self.send_config_button = QPushButton("Send Config", self)
        self.send_config_button.clicked.connect(self.send_config)
        self.layout.addWidget(self.send_config_button)

    def set_config(self, config):
        self.face_checkbox.setChecked(config.get("face_detection", False))
        self.person_checkbox.setChecked(config.get("person_detection", False))
        self.vehicle_checkbox.setChecked(config.get("vehicle_detection", False))
        self.animal_checkbox.setChecked(config.get("animal_detection", False))

    def get_config(self):
        return {
            "camera_id": self.camera_selector.currentData()[1],
            "face_detection": self.face_checkbox.isChecked(),
            "person_detection": self.person_checkbox.isChecked(),
            "vehicle_detection": self.vehicle_checkbox.isChecked(),
            "animal_detection": self.animal_checkbox.isChecked()
        }

    def send_config(self):
        parent = self.parent()
        if parent:
            parent.send_config()
            self.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("NVR Real-Time Viewer")
        self.setGeometry(100, 100, 1280, 720)
        self.setWindowIcon(QIcon("resources/download.png"))

        self.camera_index_map = {}
        self.motion_detected = {}
        self.video_displays = []
        self.media_players = {}

        self.init_ui()
        self.setup_streams()

        self.motion_thread = MotionStatusThread()
        self.motion_thread.motion_status_signal.connect(self.handle_motion_status)
        self.motion_thread.start()

    def init_ui(self):
        self.video_displays = []

        layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        header_label = QLabel("NVR Real-Time Viewer")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        top_layout.addWidget(header_label)
        top_layout.addStretch()

        layout.addLayout(top_layout)

        button_layout = QHBoxLayout()
        settings_button = QPushButton("Settings", self)
        settings_button.clicked.connect(self.show_settings_dialog)
        button_layout.addWidget(settings_button)

        refresh_button = QPushButton("Refresh", self)
        refresh_button.clicked.connect(self.refresh_streams)
        button_layout.addWidget(refresh_button)
        layout.addLayout(button_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setStyleSheet("background-color: #2E2E2E;")

        layout.addWidget(self.scroll_area)

        container = QWidget()
        container.setLayout(layout)
        container.setStyleSheet("background-color: #2E2E2E;")
        self.setCentralWidget(container)

        self.settings_dialog = SettingsDialog(self)

    def setup_streams(self):
        self.clear_layout(self.scroll_layout)
        self.settings_dialog.camera_selector.clear()
        row, col = 0, 0
        for url in NVR_SERVER_URLS:
            try:
                response = requests.get(f'{url}/cameras')
                response.raise_for_status()
                camera_ids = response.json()
                logging.debug(f"Response from NVR at {url}: {camera_ids}")
            except requests.RequestException as e:
                logging.error(f"Failed to fetch camera list from {url}: {e}")
                camera_ids = []

            for camera_id in camera_ids:
                self.settings_dialog.camera_selector.addItem(f"Camera {camera_id}", (url, camera_id))
                video_frame = self.create_video_frame(url, camera_id)
                self.scroll_layout.addWidget(video_frame, row, col)
                col += 1
                if col == 8:
                    col = 0
                    row += 1

        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def update_detection_options(self):
        selected_camera_data = self.settings_dialog.camera_selector.currentData()
        if not selected_camera_data:
            self.settings_dialog.set_config({})
        else:
            config = self.get_camera_config(selected_camera_data[1])
            self.settings_dialog.set_config(config)

    def get_camera_config(self, camera_id):
        return {
            "face_detection": self.settings_dialog.face_checkbox.isChecked(),
            "person_detection": self.settings_dialog.person_checkbox.isChecked(),
            "vehicle_detection": self.settings_dialog.vehicle_checkbox.isChecked(),
            "animal_detection": self.settings_dialog.animal_checkbox.isChecked()
        }

    def show_settings_dialog(self):
        selected_camera_data = self.settings_dialog.camera_selector.currentData()
        if selected_camera_data:
            url, camera_id = selected_camera_data
            config = self.get_camera_config(camera_id)
            self.settings_dialog.set_config(config)

        self.settings_dialog.exec_()

    def refresh_streams(self):
        self.setup_streams()

    def create_video_frame(self, url, camera_id):
        frame = QFrame()
        frame.setFrameShape(QFrame.Box)
        frame.setLineWidth(10)  # Thicker border
        frame.setStyleSheet("background-color: #3C3C3C; border: 10px solid #B0B0B0;")  # Larger background

        frame_layout = QVBoxLayout(frame)

        video_label = QLabel(f"Camera {camera_id}")
        video_label.setAlignment(Qt.AlignCenter)
        video_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        frame_layout.addWidget(video_label)

        video_widget = QVideoWidget()
        frame_layout.addWidget(video_widget)

        media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        media_player.setVideoOutput(video_widget)
        media_url = QUrl(f"{url}/video_feed/{camera_id}")
        logging.debug(f"Media URL for Camera {camera_id} at {url}: {media_url.toString()}")
        media_player.setMedia(QMediaContent(media_url))

        if not media_player.isAvailable():
            logging.error(f"Media player for Camera {camera_id} at {url} is not available.")
            error_label = QLabel(f"Unable to stream from Camera {camera_id} at {url}")
            error_label.setAlignment(Qt.AlignCenter)
            frame_layout.addWidget(error_label)
        else:
            media_player.error.connect(lambda: self.handle_error(camera_id, url, media_player))
            media_player.play()

        self.camera_index_map[camera_id] = media_player
        self.video_displays.append(video_widget)

        return frame

    def handle_error(self, camera_id, url, media_player):
        error_message = media_player.errorString()
        logging.error(f"Error for Camera {camera_id} at {url}: {error_message}")
        error_label = QLabel(f"Error for Camera {camera_id} at {url}: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: red;")
        self.scroll_layout.addWidget(error_label)

    def show_error_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText(message)
        msg_box.setWindowTitle("Camera Error")
        msg_box.exec_()

    def handle_motion_status(self, motion_status):
        logging.debug(f"Received motion status: {motion_status}")
        for camera_id, detected in motion_status.items():
            self.update_motion_frame(camera_id, detected)

    def update_motion_frame(self, camera_id, detected):
        logging.debug(f"Updating display for Camera {camera_id}, Detected: {detected}")
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget and isinstance(widget, QFrame):
                    frame = widget
                    label = frame.findChild(QLabel)
                    logging.debug(f"Checking frame: {label.text() if label else 'No label'}")
                    if label and f"Camera {camera_id}" in label.text():
                        if detected:
                            logging.debug(f"Motion detected for Camera {camera_id}, changing background to blue")
                            frame.setStyleSheet("background-color: #87CEEB; border: 10px solid #B0B0B0;")  # Thicker border for motion detection
                        else:
                            logging.debug(f"No motion detected for Camera {camera_id}, resetting background")
                            frame.setStyleSheet("background-color: #3C3C3C; border: 10px solid #B0B0B0;")

    def send_config(self):
        selected_camera_data = self.settings_dialog.camera_selector.currentData()
        if not selected_camera_data:
            self.show_error_message("No camera selected.")
            return

        url, camera_id = selected_camera_data
        config = self.settings_dialog.get_config()
        config["camera_id"] = camera_id  # Ensure camera_id is included

        logging.debug(f"Sending config to {url} for Camera {camera_id}: {config}")

        try:
            response = requests.post(f'{url}/config', json=config)
            response.raise_for_status()
            logging.debug(f"Config sent to {url} for Camera {camera_id}: {config}")
            logging.debug(f"Response content: {response.content.decode()}")
            self.refresh_streams()
            self.settings_dialog.accept()
        except requests.RequestException as e:
            logging.error(f"Failed to send config to {url}: {e}")
            if e.response is not None:
                logging.error(f"Response content: {e.response.content.decode()}")

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
