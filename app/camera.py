import cv2

class Camera:
    def __init__(self, camera_id):
        self.camera_id = camera_id
        self.capture = cv2.VideoCapture(camera_id)
        self.connected = self.capture.isOpened()
        if not self.connected:
            print(f"Warning: Camera with ID {camera_id} cannot be opened")

    def get_frame(self):
        if not self.connected:
            return None
        ret, frame = self.capture.read()
        if not ret:
            return None
        return frame
