import cv2
from explosion_detection import CombinedDetector

def main():
    detector = CombinedDetector(
        yolov3_cfg='/home/risc3/new_nvring/NVRR/nvr1_project/yolo/yolov3.cfg',
        yolov3_weights='/home/risc3/new_nvring/NVRR/nvr1_project/yolo/yolov3.weights',
        explosion_conf_threshold=0.2,  
        person_conf_threshold=0.4,     # Confidence threshold for people
        animal_conf_threshold=0.4,     # Confidence threshold for animals
        car_conf_threshold=0.4,        # Confidence threshold for cars
        bird_conf_threshold=0.4,       # Confidence threshold for birds
        ship_conf_threshold=0.4        # Confidence threshold for ships
    )

    # Path to the video file (set to 0 for webcam)
    video_path = '/home/risc3/new_nvring/NVRR/vid/longazzvid.mp4'  # Replace with your video file path
    # video_path = 0  # Uncomment to use webcam

    # Open the video file or webcam
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file or webcam.")
        return

    cv2.namedWindow('Explosion, Person, Animal, Car, Bird, and Ship Detection', cv2.WINDOW_NORMAL)
    frame_count = 0  
    last_processed_frame = None 
    fps = int(cap.get(cv2.CAP_PROP_FPS))  

    frame_count = 0  
    last_processed_frame = None  

    while True:
        ret, frame = cap.read()
        if not ret:
            print("End of video reached or error reading frame.")
            break

        if frame_count % 6 == 0:
            last_processed_frame = detector.detect_and_draw(frame)
        
        frame_to_show = last_processed_frame if last_processed_frame is not None else frame

        cv2.imshow('Explosion, Person, Animal, Car, Bird, and Ship Detection', frame_to_show)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):  
            break
        elif key == ord('f'):  
            current_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos + 10 * fps)
        elif key == ord('b'):  
            current_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(current_pos - 10 * fps, 0))

        frame_count += 1  
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
