import sys
import threading
from PyQt5.QtWidgets import QApplication
from app.main_window import MainWindow, app, main_window
import argparse
from flask import Flask, jsonify, request
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create a threading event to synchronize the initialization
init_event = threading.Event()

def start_qt_app(camera_id):
    global main_window
    qapp = QApplication(sys.argv)
    main_window = MainWindow(camera_id)
    init_event.set()
    qapp.exec_()

def start_flask_app(port):
    init_event.wait()
    app.run(host='0.0.0.0', port=port)

@app.route('/config', methods=['POST'])
def set_config():
    global main_window
    data = request.get_json()
    logging.debug(f"Received config data: {data}")
    if not data:
        return jsonify({"error": "No data received"}), 400
    
    camera_id = data.get('camera_id')
    if camera_id is None:
        return jsonify({"error": "camera_id is required"}), 400

    try:
        main_window.enable_face_detection[camera_id] = data.get('face_detection', False)
        main_window.enable_person_detection[camera_id] = data.get('person_detection', False)
        main_window.enable_vehicle_detection[camera_id] = data.get('vehicle_detection', False)
        main_window.enable_animal_detection[camera_id] = data.get('animal_detection', False)

        main_window.save_camera_settings(
            main_window.settings_dir + f'/camera_{camera_id}.py',
            camera_id,
            main_window.thresholds[camera_id],
            main_window.enable_face_detection[camera_id],
            main_window.enable_person_detection[camera_id],
            main_window.enable_vehicle_detection[camera_id],
            main_window.enable_animal_detection[camera_id]
        )
        return jsonify({"status": "Configuration updated"})
    except Exception as e:
        logging.error(f"Error in set_config: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_config', methods=['GET'])
def get_config():
    global main_window
    camera_id = request.args.get('camera_id')
    if not camera_id:
        return jsonify({"error": "camera_id is required"}), 400

    try:
        face_detection = 'ON' if main_window.enable_face_detection[camera_id] else 'OFF'
        person_detection = 'ON' if main_window.enable_person_detection[camera_id] else 'OFF'
        vehicle_detection = 'ON' if main_window.enable_vehicle_detection[camera_id] else 'OFF'
        animal_detection = 'ON' if main_window.enable_animal_detection[camera_id] else 'OFF'
        config_string = f"{face_detection}, {person_detection}, {vehicle_detection}, {animal_detection}"
        return jsonify({"config": config_string})
    except Exception as e:
        logging.error(f"Error in get_config: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='NVR Application')
    parser.add_argument('--camera_id', type=int, default=0, help='Camera ID')
    parser.add_argument('--port', type=int, default=5001, help='Port number')
    args = parser.parse_args()

    qt_thread = threading.Thread(target=start_qt_app, args=(args.camera_id,))
    flask_thread = threading.Thread(target=start_flask_app, args=(args.port,))

    qt_thread.start()
    flask_thread.start()

    qt_thread.join()
    flask_thread.join()

