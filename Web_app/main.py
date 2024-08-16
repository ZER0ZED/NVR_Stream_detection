import sys
import subprocess
import socket
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui.main_window import MainWindow

NVR_COMMANDS = [
    ["/bin/python3", "/home/risc3/new_nvring/NVRR/nvr1_project/main.py", "--camera_id", "2", "--port", "5002"],
    ["/bin/python3", "/home/risc3/new_nvring/NVRR/nvr1_project/main.py", "--camera_id", "0", "--port", "5001"]
]

processes = []

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    result = subprocess.run(['sudo', 'lsof', '-t', '-i', f':{port}'], stdout=subprocess.PIPE, text=True)
    pids = result.stdout.strip().split('\n')
    for pid in pids:
        if pid:
            subprocess.run(['sudo', 'kill', '-9', pid])
            print(f"Killed process {pid} on port {port}")

def ensure_ports_are_free():
    ports = [5001, 5002]
    for port in ports:
        if is_port_in_use(port):
            print(f"Port {port} is in use. Trying to free the port...")
            kill_process_on_port(port)
            if is_port_in_use(port):
                print(f"Failed to free port {port}.")
                return False
    return True

def run_initial_commands():
    global processes
    for command in NVR_COMMANDS:
        port = int(command[-1])
        if is_port_in_use(port):
            print(f"Port {port} is in use. Trying to free the port...")
            kill_process_on_port(port)
            if is_port_in_use(port):
                print(f"Failed to free port {port}.")
                return False
        print(f"Starting NVR command: {' '.join(command)}")
        p = subprocess.Popen(command)
        processes.append(p)
    return processes

def cleanup_processes():
    global processes
    for p in processes:
        p.terminate()
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
    processes = []

class StreamApp(QMainWindow):
    def __init__(self):
        super(StreamApp, self).__init__()
        self.main_window = MainWindow()
        self.setCentralWidget(self.main_window)
        self.setGeometry(100, 100, 1280, 720)
        self.setWindowTitle("NVR Real-Time Viewer")
    
    def closeEvent(self, event):
        cleanup_processes()
        super(StreamApp, self).closeEvent(event)

def main():
    # Ensure ports 5001 and 5002 are free
    if not ensure_ports_are_free():
        print("Failed to ensure ports are free.")
        return

    # Run the initial commands to start the NVR applications
    if not run_initial_commands():
        print("Failed to start NVR applications.")
        return

    # Start the stream application
    print("Starting the stream application...")
    app = QApplication(sys.argv)
    window = StreamApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
