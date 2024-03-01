import abc
import logging
import os
import time
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pyvisa
from filelock import FileLock

# Import classes and modules from device module as needed.
from device.data import DataBuffer, DataSource
from device.device import Device, DeviceDetector, MockDevice
from device.dg4202 import DG4202, DG4202DataSource, DG4202Mock
from device.edux1002a import EDUX1002A, EDUX1002ADataSource, EDUX1002AMock
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
    device_type = Device
    device_type_mock = MockDevice

    def __init__(
        self,
        state_manager: StateManager,
        args_dict: dict,
        resource_manager: pyvisa.ResourceManager,
    ):
        self.state_manager = state_manager
        self.args_dict = args_dict
        self.rm = resource_manager
        self.mock_device = self.device_type_mock()
        self.mock_device.killed = False
        self.setup_device()
        self.setup_data()

    def setup_device(self):
        if self.args_dict.get("hardware_mock", False):
            self.device = self.mock_device
        else:
            self.fetch_hardware()

    def fetch_hardware(self) -> None:
        """Fetch and update the device driver (hardware, not simulated!)"""
        self.device: Device = DeviceDetector(
            resource_manager=self.rm, device_type=self.device_type
        ).detect_device()

    def setup_data(self):
        # Will still return a valid dictionary even if self.device is None
        raise NotImplementedError("Must be implemented in subclasses.")
        self.data_source = DataSource(self.device)

    def update_last_alive_state(self, last_alive_key: str, alive: bool) -> None:
        """
        Updates the 'last_alive' timestamp in the state for the device.

        Parameters:
            last_alive_key (str): The key in the state dict corresponding to the device's last alive timestamp.
            alive (bool): Indicates whether the device is considered alive or not.
        """
        state = self.state_manager.read_state()
        if alive:
            state[last_alive_key] = time.time()
        else:
            state[last_alive_key] = None
        self.state_manager.write_state(state)

    def get_device(self) -> Union[Device, MockDevice, None]:
        last_alive_key = f"{self.device_type.IDN_STRING}_last_alive"

        # Decide if we should use a mock device or try to fetch a real device.
        use_mock = self.args_dict.get("hardware_mock", False)

        if use_mock:
            self.device = self.mock_device if not self.mock_device.killed else None
        else:
            self.fetch_hardware()  # This attempts to set `self.device` to a real device.
        # Determine if the device is considered 'alive'.
        device_alive = self.device is not None and (
            not isinstance(self.device, MockDevice) or not self.device.killed
        )

        # Update the 'last_alive' state accordingly.
        self.update_last_alive_state(last_alive_key, device_alive)
        self.setup_data()
        return self.device

    def set_mock_state(self, state: bool) -> None:
        self.mock_device.killed = state

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
                        f"{method_name} is not a method of {self.device.IDN_STRING}"
                    )
            except AttributeError as e:
                logging.error(
                    f"Method {method_name} not found on device {self.device.IDN_STRING}: {e}"
                )
                return None
        else:
            logging.error(f"No device instance available for {self.device.IDN_STRING}")
            return None

    def is_device_alive(self) -> bool:
        try:
            if self.args_dict["hardware_mock"]:
                return not self.device.killed
            idn = self.device.interface.read("*IDN?")
            return self.device.IDN_STRING in idn
        except Exception as e:
            return False

    def write_device_state(self) -> None:
        alive = self.is_device_alive()
        if alive:
            self.state_manager.update_device_last_alive(
                self.device.IDN_STRING, time.time()
            )
        else:
            self.state_manager.update_device_last_alive(self.device.IDN_STRING, None)

    def get_device_uptime(self) -> str:
        last_alive = self.state_manager.get_device_last_alive(self.device.IDN_STRING)
        if last_alive:
            uptime_seconds = time.time() - last_alive
            return str(timedelta(seconds=int(uptime_seconds)))
        else:
            return "N/A"


class DG4202Manager(DeviceManagerBase):
    device_type = DG4202
    device_type_mock = DG4202Mock

    def __init__(
        self,
        state_manager: StateManager,
        args_dict: dict,
        resource_manager: pyvisa.ResourceManager,
    ):
        super().__init__(state_manager, args_dict, resource_manager)

    def setup_data(self):
        # Will still return a valid dictionary even if self.device is None
        self.data_source = DG4202DataSource(self.device)

    def get_data(self) -> dict:
        return self.data_source.query_data()


class EDUX1002AManager(DeviceManagerBase):
    device_type = EDUX1002A
    device_type_mock = EDUX1002AMock

    def __init__(
        self,
        state_manager: StateManager,
        args_dict: dict,
        resource_manager: pyvisa.ResourceManager,
        buffer_size: int,
    ):
        self.buffer_size = buffer_size
        super().__init__(state_manager, args_dict, resource_manager)

    def setup_data(self):
        self.data_source = (
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

    def update_buffer(self, channel: int) -> None:
        if self.data_source:
            self.data_source[channel].update()

    def get_data(self, channel: int) -> dict:
        return self.data_source[channel].get_data() if self.device else None
