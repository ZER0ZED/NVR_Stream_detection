import subprocess
import time

def is_port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    result = subprocess.run(['sudo', 'lsof', '-t', '-i', f':{port}'], stdout=subprocess.PIPE, text=True)
    pids = result.stdout.strip().split('\n')
    for pid in pids:
        if pid:
            subprocess.run(['sudo', 'kill', '-9', pid])
            print(f"Killed process {pid} on port {port}")
            time.sleep(1)  # Wait a moment to allow the process to terminate

def close_ports(ports):
    for port in ports:
        if is_port_in_use(port):
            print(f"Port {port} is in use. Trying to free the port...")
            kill_process_on_port(port)
            time.sleep(2)  # Wait a bit longer after killing the process to check the port again
            if is_port_in_use(port):
                print(f"Failed to free port {port}.")
            else:
                print(f"Port {port} is now free.")
        else:
            print(f"Port {port} is already free.")

if __name__ == '__main__':
    ports_to_close = [5001, 5002]
    close_ports(ports_to_close)
