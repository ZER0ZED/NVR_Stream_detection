import cv2

class MotionDetector:
    def __init__(self, threshold=1000):
        self.back_sub = cv2.createBackgroundSubtractorMOG2()
        self.threshold = threshold

    def detect(self, frame):
        fg_mask = self.back_sub.apply(frame)

        # Remove noise
        fg_mask = cv2.medianBlur(fg_mask, 5)

        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < self.threshold:
                continue
            return True
        return False
