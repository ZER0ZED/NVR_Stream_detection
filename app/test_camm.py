import cv2

def capture_and_display(left_camera_index, right_camera_index):
    cap_left = cv2.VideoCapture(left_camera_index)
    cap_right = cv2.VideoCapture(right_camera_index)

    if not cap_left.isOpened() or not cap_right.isOpened():
        print("Error: Could not open one or both of the cameras.")
        return

    while True:
        ret_left, frame_left = cap_left.read()
        ret_right, frame_right = cap_right.read()

        if not ret_left or not ret_right:
            print("Error: Could not read frame from one or both of the cameras.")
            break

        # Display frames
        cv2.imshow('Left Camera (Index 0)', frame_left)
        cv2.imshow('Right Camera (Index 2)', frame_right)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_and_display(left_camera_index=0, right_camera_index=2)
