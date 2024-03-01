import abc
import logging
import os
import time
from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pyvisa
from filelock import FileLock

# Import classes and modules from device module as needed.
from device.data import DataBuffer
from device.device import Device
from device.dg4202 import DG4202, DG4202DataSource, DG4202Detector, DG4202Mock
from device.edux1002a import (
    EDUX1002A,
    EDUX1002ADataSource,
    EDUX1002ADetector,
    EDUX1002AMock,
)
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


class DeviceManagerBase(abc.ABC):
    device_type = "managed_device"
    IDN_STRING = "IDN_STRING"

    def __init__(
        self,
        state_manager: StateManager,
        args_dict: dict,
        resource_manager: pyvisa.ResourceManager,
    ):
        self.state_manager = state_manager
        self.device: Device = None
        self.args_dict = args_dict
        self.rm = resource_manager
        self._mock_device = MagicMock()
        self._mock_device.killed = False

    def call_device_method(self, method_name: str, *args, **kwargs):
        """
        Generic method to call a method on the managed device.

        :param method_name: The name of the method to be called on the device.
        :param args: Positional arguments to pass to the device method.
        :param kwargs: Keyword arguments to pass to the device method.
        :return: The result of the device method call.
        """
        self.device = self.get_device()  # Ensure we have the current device instance
        if self.device is not None:
            try:
                method = getattr(self.device, method_name)
                if callable(method):
                    return method(*args, **kwargs)
                else:
                    raise AttributeError(
                        f"{method_name} is not a method of {self.device_type}"
                    )
            except AttributeError as e:
                logging.error(
                    f"Method {method_name} not found on device {self.device_type}: {e}"
                )
                return None
        else:
            logging.error(f"No device instance available for {self.device_type}")
            return None

    def is_device_alive(self) -> bool:
        try:
            if self.args_dict["hardware_mock"]:
                return not self.device.killed
            idn = self.device.interface.read("*IDN?")
            return self.IDN_STRING in idn
        except Exception as e:
            return False

    def get_device(self):
        raise NotImplementedError("Must be implemented in subclasses.")

    def update_device_state(self):
        alive = self.is_device_alive()
        if alive:
            self.state_manager.update_device_last_alive(self.device_type, time.time())
        else:
            self.state_manager.update_device_last_alive(self.device_type, None)

    def get_device_uptime(self) -> str:
        last_alive = self.state_manager.get_device_last_alive(self.device_type)
        if last_alive:
            uptime_seconds = time.time() - last_alive
            return str(timedelta(seconds=int(uptime_seconds)))
        else:
            return "N/A"


class DG4202Manager(DeviceManagerBase):
    device_type = "dg"
    IDN_STRING = "DG4202"

    def __init__(
        self,
        state_manager: StateManager,
        args_dict: dict,
        resource_manager: pyvisa.ResourceManager,
    ):
        super().__init__(state_manager, args_dict, resource_manager)
        self._mock_device = DG4202Mock()
        self.data_source = None
        self._initialize_device()

    def _initialize_device(self):
        if self.args_dict["hardware_mock"]:
            self.device: DG4202Mock = self._mock_device
        else:
            self.device: DG4202 = DG4202Detector(
                resource_manager=self.rm
            ).detect_device()

        self.data_source = DG4202DataSource(self.device)

    def get_device(self) -> DG4202:
        state = self.state_manager.read_state()
        if self.args_dict["hardware_mock"]:
            if self._mock_device.killed:
                state["dg_last_alive"] = None
                self.state_manager.write_state(state)
                self.device = None
            else:
                if state.get("dg_last_alive") is None:
                    state["dg_last_alive"] = time.time()
                self.state_manager.write_state(state)
                self.device: DG4202Mock = self._mock_device
        else:
            self.device: DG4202 = DG4202Detector(
                resource_manager=self.rm
            ).detect_device()
            if self.device is None:
                state["dg_last_alive"] = None
            else:
                if state.get("dg_last_alive") is None:
                    state["dg_last_alive"] = time.time()
            self.state_manager.write_state(state)
        self.data_source = DG4202DataSource(self.device)

        return self.device

    def get_data(self) -> dict:
        return self.data_source.query_data()


class EDUX1002AManager(DeviceManagerBase):
    device_type = "edux"
    IDN_STRING = "EDU-X 1002A"

    def __init__(
        self,
        state_manager: StateManager,
        args_dict: dict,
        resource_manager: pyvisa.ResourceManager,
        buffer_size: int,
    ):
        super().__init__(state_manager, args_dict, resource_manager)
        self._mock_device = EDUX1002AMock()
        self.buffers = {1: None, 2: None}
        self.buffer_size = buffer_size
        self._initialize_device()

    def _initialize_device(self):
        detector = EDUX1002ADetector(resource_manager=self.rm)
        if self.args_dict["hardware_mock"]:
            self.device: EDUX1002AMock = self._mock_device
        else:
            self.device: EDUX1002A = detector.detect_device()
        self.buffers = (
            {
                1: DataBuffer(EDUX1002ADataSource(self.device, 1), self.buffer_size),
                2: DataBuffer(EDUX1002ADataSource(self.device, 2), self.buffer_size),
            }
            if self.device
            else {
                1: None,
                2: None,
            }
        )

    def get_device(self) -> EDUX1002A:
        state = self.state_manager.read_state()
        if self.args_dict["hardware_mock"]:
            if self._mock_device.killed:
                state["edux_last_alive"] = None
                self.state_manager.write_state(state)
                self.device = None
            else:
                if state.get("edux_last_alive") is None:
                    state["edux_last_alive"] = time.time()
                self.state_manager.write_state(state)
                self.device: EDUX1002AMock = self._mock_device
        else:
            self.device = EDUX1002ADetector(resource_manager=self.rm).detect_device()
            if self.device is None:
                state["edux_last_alive"] = None
            else:
                if state.get("edux_last_alive") is None:
                    state["edux_last_alive"] = time.time()
            self.state_manager.write_state(state)
        self.data_source = EDUX1002ADataSource(self.device)
        return self.device

    def get_data(self, channel: int) -> dict:
        return self.buffers[channel].get_data() if self.device else None
