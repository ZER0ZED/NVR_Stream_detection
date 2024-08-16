import os
import cv2
import numpy as np
import time

class VehicleDetector:
    def __init__(self):
        yolo_config = os.path.join(os.path.dirname(__file__), '..', 'yolo', 'yolov3-tiny.cfg')
        yolo_weights = os.path.join(os.path.dirname(__file__), '..', 'yolo', 'yolov3-tiny.weights')
        coco_names = os.path.join(os.path.dirname(__file__), '..', 'yolo', 'coco.names')
        
        self.net = cv2.dnn.readNet(yolo_weights, yolo_config)
        self.layer_names = self.net.getLayerNames()
        self.output_layers = [self.layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]

        with open(coco_names, "r") as f:
            self.classes = [line.strip() for line in f.readlines()]
        
        self.last_detection_time = 0
        self.last_detected_box = None
        self.focus_duration = 3  # seconds
        self.detection_interval = 1  # seconds

    def detect_and_draw(self, frame):
        current_time = time.time()

        # Check if enough time has passed since the last detection
        if current_time - self.last_detection_time < self.detection_interval:
            # Draw the last detected box if within focus duration
            if self.last_detected_box and (current_time - self.last_detection_time <= self.focus_duration):
                x, y, w, h, label = self.last_detected_box
                cv2.rectangle(frame, (int(x), int(y)), (int(x + w), int(y + h)), (0, 255, 0), 2)
                cv2.putText(frame, label, (int(x), int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            return frame
        
        height, width = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)

        class_ids = []
        confidences = []
        boxes = []

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if self.classes[class_id] in ["car", "bus", "truck", "motorbike"] and confidence > 0.39:
                    # Object detected
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

        if len(indexes) > 0:
            if isinstance(indexes[0], list):
                indexes = [i[0] for i in indexes]
            max_conf_index = indexes[0]
            x, y, w, h = boxes[max_conf_index]
            label = str(self.classes[class_ids[max_conf_index]])
            self.last_detected_box = (x, y, w, h, label)
            self.last_detection_time = current_time
        
        # Draw the last detected box if within focus duration
        if self.last_detected_box and (current_time - self.last_detection_time <= self.focus_duration):
            x, y, w, h, label = self.last_detected_box
            cv2.rectangle(frame, (int(x), int(y)), (int(x + w), int(y + h)), (0, 255, 0), 2)
            cv2.putText(frame, label, (int(x), int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame
