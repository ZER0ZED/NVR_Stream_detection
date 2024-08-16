import cv2
import torch
import numpy as np

class CombinedDetector:
    def __init__(self, explosion_model_path='/home/risc3/new_nvring/NVRR/nvr1_project/yolov5/best.pt', 
                 yolov3_cfg='/path/to/yolov3.cfg', yolov3_weights='/path/to/yolov3.weights', 
                 explosion_conf_threshold=0.5, person_conf_threshold=0.5, animal_conf_threshold=0.5, 
                 car_conf_threshold=0.5, bird_conf_threshold=0.5, ship_conf_threshold=0.5):
        # Initialize YOLOv5 for explosion detection
        self.explosion_model = torch.hub.load('ultralytics/yolov5', 'custom', path=explosion_model_path)
        self.explosion_model.eval()
        self.explosion_conf_threshold = explosion_conf_threshold  # Explosion confidence threshold

        # Initialize YOLOv3 for detecting persons, animals, cars, birds, and ships
        self.yolov3_net = cv2.dnn.readNetFromDarknet(yolov3_cfg, yolov3_weights)
        self.yolov3_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.yolov3_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        self.yolov3_layer_names = self.yolov3_net.getLayerNames()
        self.yolov3_output_layers = [self.yolov3_layer_names[i - 1] for i in self.yolov3_net.getUnconnectedOutLayers()]

        self.person_conf_threshold = person_conf_threshold 
        self.animal_conf_threshold = animal_conf_threshold 
        self.car_conf_threshold = car_conf_threshold 
        self.bird_conf_threshold = bird_conf_threshold 
        self.ship_conf_threshold = ship_conf_threshold 

        self.person_class_id = 0
        self.animal_class_ids = [15, 16, 17, 18, 19, 20, 21, 22, 23]
        self.car_class_ids = [2, 5, 7]
        self.bird_class_ids = [14]
        self.ship_class_ids = [8]

    def detect_explosions(self, frame):


        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.explosion_model(img)

        detections = results.xyxy[0].numpy()  # Get the detections

        for det in detections:
            x1, y1, x2, y2, conf, cls = det
            label = self.explosion_model.names[int(cls)]
            if label == 'Explosion' and conf > self.explosion_conf_threshold:  # Check confidence threshold
                # Draw bounding box around detected explosion
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                cv2.putText(frame, f'{label} {conf:.2f}', (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        return frame

    def detect_objects(self, frame):

        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.yolov3_net.setInput(blob)
        outputs = self.yolov3_net.forward(self.yolov3_output_layers)

        h, w = frame.shape[:2]
        boxes = []
        confidences = []
        class_ids = []

        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                # Check confidence against the respective thresholds and valid class IDs
                if (class_id == self.person_class_id and confidence > self.person_conf_threshold) or \
                (class_id in self.animal_class_ids and confidence > self.animal_conf_threshold) or \
                (class_id in self.car_class_ids and confidence > self.car_conf_threshold) or \
                (class_id in self.bird_class_ids and confidence > self.bird_conf_threshold) or \
                (class_id in self.ship_class_ids and confidence > self.ship_conf_threshold):
                    box = detection[0:4] * np.array([w, h, w, h])
                    (centerX, centerY, width, height) = box.astype("int")
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))

                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indices = cv2.dnn.NMSBoxes(boxes, confidences, min(self.person_conf_threshold, self.animal_conf_threshold, self.car_conf_threshold, self.bird_conf_threshold, self.ship_conf_threshold), 0.4)

        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                conf_percent = int(confidences[i] * 100)  # Convert confidence to percentage

                if class_ids[i] == self.person_class_id:
                    label = f"Person {conf_percent}%"
                    color = (225, 255, 255)
                elif class_ids[i] in self.animal_class_ids:
                    label = f"Animal {conf_percent}%"
                    color = (225, 255, 255)
                elif class_ids[i] in self.car_class_ids:
                    label = f"Car {conf_percent}%"
                    color = (225, 255, 255)
                elif class_ids[i] in self.bird_class_ids:
                    label = f"Bird {conf_percent}%"
                    color = (225, 255, 255)
                elif class_ids[i] in self.ship_class_ids:
                    label = f"Ship {conf_percent}%"
                    color = (225, 255, 255)

                # Draw the bounding box
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

                # Put the label above the rectangle with a smaller font and blue color
                font_scale = 0.8  # Smaller font scale, less than 10
                thickness = 2
                text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
                text_x = x
                text_y = y - 5  # Position the text above the rectangle
                if text_y < 0:
                    text_y = y + text_size[1] + 5  # If text is outside the frame, position it inside
                cv2.putText(frame, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 0, 0), thickness)  # Blue color

        return frame


    def detect_and_draw(self, frame):
  
        frame = self.detect_explosions(frame)
        frame = self.detect_objects(frame)
        return frame


