import logging
import os
import time
from datetime import timedelta
from pathlib import Path
from filelock import FileLock
from utils import logging as logutils



# Setting up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

class StateManager:
    def __init__(self, json_file: Path = None):
        self.json_file = json_file or Path(os.getenv("DATA"), "state.json")
        self.lock_file = self.json_file.with_suffix(".lock")
        self.data = self.default_state()
        self.birthdate = time.time()

    def read_state(self) -> dict:
        with FileLock(self.lock_file, timeout=10):
            # Utilize the load_json_with_backup utility function with locking
            self.data = (
                logutils.load_json_with_backup(self.json_file) or self.default_state()
            )
        return self.data

    def write_state(self, state: dict):
        with FileLock(self.lock_file, timeout=10):
            self.data.update(state)
            logutils.save_json(self.data, self.json_file)

    def default_state(self):
        return {}

    def update_device_last_alive(self, device_type: str, last_alive_time=None):
        state = self.read_state()
        key = f"{device_type}_last_alive"
        state[key] = last_alive_time or time.time()
        self.write_state(state)

    def get_device_last_alive(self, device_type: str):
        state = self.read_state()
        return state.get(f"{device_type}_last_alive")

    def get_uptime(self) -> str:
        uptime_seconds = time.time() - self.birthdate
        return str(timedelta(seconds=int(uptime_seconds)))