import cv2

def list_cameras(max_cameras=5):
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Camera {i} is available.")
            cap.release()
        else:
            print(f"Camera {i} is not available.")

list_cameras()
