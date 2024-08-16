import cv2
import numpy as np
from face_detector import FaceDetector
import time

class StereoVisionDepthEstimator:
    def __init__(self, baseline, focal_length, earth_radius=6371000):
        self.baseline = baseline  # Distance between cameras in meters
        self.focal_length = focal_length  # Focal length in pixels
        self.earth_radius = earth_radius

    def calculate_disparity(self, left_img, right_img):
        # Convert images to grayscale
        if len(left_img.shape) == 3:
            left_img = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
        if len(right_img.shape) == 3:
            right_img = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)

        # Create stereo block matcher
        stereo = cv2.StereoBM_create(numDisparities=64, blockSize=15)  # Increased numDisparities for better results
        disparity = stereo.compute(left_img, right_img).astype(np.float32) / 16.0

        return disparity

    def calculate_distance(self, disparity, x, y):
        if disparity[y, x] <= 0:
            return float('inf')

        distance = (self.baseline * self.focal_length) / disparity[y, x]
        corrected_distance = self.correct_for_earth_curvature(distance)

        return corrected_distance

    def correct_for_earth_curvature(self, distance):
        h = distance**2 / (2 * self.earth_radius)
        corrected_distance = distance + h
        return corrected_distance

def main():
    # Initialize camera
    left_camera_index = 0
    right_camera_index = 2
    cap_left = cv2.VideoCapture(left_camera_index)
    cap_right = cv2.VideoCapture(right_camera_index)

    # Initialize depth estimator and face detector
    baseline = 0.3  # 30 cm
    focal_length = 700  # Focal length in pixels
    depth_estimator = StereoVisionDepthEstimator(baseline, focal_length)
    face_detector = FaceDetector()

    last_print_time = time.time()

    while True:
        ret_left, frame_left = cap_left.read()
        ret_right, frame_right = cap_right.read()
        if not ret_left or not ret_right:
            print("Error reading frames from cameras")
            break

        # Detect faces in the left image
        results = face_detector.detect_faces(frame_left)

        # Get bounding box coordinates from face detection
        h, w, _ = frame_left.shape

        if results.detections:
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                x_min = int(bboxC.xmin * w)
                y_min = int(bboxC.ymin * h)
                x_max = x_min + int(bboxC.width * w)
                y_max = y_min + int(bboxC.height * h)

                # Calculate the disparity map
                disparity = depth_estimator.calculate_disparity(frame_left, frame_right)

                # Display the disparity map for debugging
                disp_normalized = cv2.normalize(disparity, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                cv2.imshow('Disparity Map', disp_normalized)

                # Calculate the average depth within the bounding box
                bbox_depth = disparity[y_min:y_max, x_min:x_max]
                valid_depths = bbox_depth[bbox_depth > 0]  # Filter out invalid disparity values
                if valid_depths.size > 0:
                    avg_disparity = np.mean(valid_depths)
                    avg_depth_m = depth_estimator.calculate_distance(disparity, x_min, y_min)
                    avg_depth_cm = avg_depth_m * 100
                    distance_text = f"{avg_depth_cm:.2f} cm"
                else:
                    distance_text = "inf"

                # Print distance information every 2 seconds
                current_time = time.time()
                if current_time - last_print_time >= 2:
                    print(f"Face detected at distance: {distance_text}")
                    last_print_time = current_time

        # Display the result
        cv2.imshow('Distance Measurement', frame_left)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.1)  # Add a small delay to reduce CPU usage and give time for processing

    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
