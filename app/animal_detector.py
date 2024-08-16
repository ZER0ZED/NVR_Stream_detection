# app/animal_detector.py

import os
import cv2
import numpy as np
import logging

class AnimalDetector:
    def __init__(self):
        yolo_config = os.path.join(os.path.dirname(__file__), '..', 'yolo', 'yolov3-tiny.cfg')
        yolo_weights = os.path.join(os.path.dirname(__file__), '..', 'yolo', 'yolov3-tiny.weights')
        coco_names = os.path.join(os.path.dirname(__file__), '..', 'yolo', 'coco.names')
        
        self.net = cv2.dnn.readNet(yolo_weights, yolo_config)
        self.layer_names = self.net.getLayerNames()
        self.output_layers = [self.layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]

        with open(coco_names, "r") as f:
            self.classes = [line.strip() for line in f.readlines()]

        self.animal_classes = ["cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"]
        logging.basicConfig(level=logging.DEBUG)

    def detect_and_draw(self, frame):
        """
        Detects animals in the frame and draws bounding boxes.
        
        :param frame: The input frame from the camera.
        :return: The frame with drawn bounding boxes.
        """
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
                if self.classes[class_id] in self.animal_classes and confidence > 0.5:
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
        logging.debug(f"Detections: {len(boxes)}, After NMS: {len(indexes)}")
        
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure coordinates are integers

                label = str(self.classes[class_ids[i]])
                logging.debug(f"Detected {label} with confidence {confidences[i]:.2f} at ({x}, {y}, {w}, {h})")
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return frame
