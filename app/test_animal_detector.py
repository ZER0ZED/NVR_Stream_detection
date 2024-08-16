import cv2
import os
from animal_detector import AnimalDetector

def main():
    # Initialize AnimalDetector
    animal_detector = AnimalDetector()
    
    # Open the first camera (camera index 0)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break
        
        # Resize frame for faster processing
        frame = cv2.resize(frame, (640, 480))
        
        # Detect and draw animals
        frame = animal_detector.detect_and_draw(frame)
        
        # Display the resulting frame
        cv2.imshow('Animal Detection', frame)
        
        # Exit the loop when 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the camera and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
