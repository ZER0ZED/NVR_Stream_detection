# network/fetch_snapshots.py

import requests
from config import NVR_SERVER_URL

def fetch_snapshots_list():
    response = requests.get(f'{NVR_SERVER_URL}/snapshots')
    if response.status_code == 200:
        return response.json().get('snapshots', [])
    return []

def fetch_snapshot(filename):
    response = requests.get(f'{NVR_SERVER_URL}/snapshots/{filename}', stream=True)
    if response.status_code == 200:
        return response.content
    return None
