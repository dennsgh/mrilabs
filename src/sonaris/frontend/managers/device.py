import abc
import logging
import time
from datetime import timedelta
from typing import Type, Union

import pyvisa

# Import classes and modules from sonaris.device module as needed.
from sonaris.device.data import DataSource
from sonaris.device.device import Device, DeviceDetector, MockDevice
from sonaris.frontend.managers.state_manager import StateManager
from sonaris.utils.log import get_logger

logger = get_logger()


class DeviceManager(abc.ABC):
    device_type: Type[Device] = Device
    mock_device_type: Type[MockDevice] = MockDevice

    def __init__(
        self,
        state_manager: StateManager,
        args_dict: dict,
        resource_manager: pyvisa.ResourceManager,
    ):
        self.state_manager = state_manager
        self.args_dict = args_dict
        self.resource_manager = resource_manager
        self.mock_device = self.mock_device_type()
        self.setup_device()
        self.setup_data()

    def setup_device(self) -> None:
        if self.args_dict.get("hardware_mock", False):
            self.fetch_mock_hardware()
        else:
            self.fetch_hardware()

    def fetch_hardware(self) -> None:
        """Fetch and update the device driver (hardware, not simulated!)"""
        self.device = DeviceDetector(
            resource_manager=self.resource_manager, device_type=self.device_type
        ).detect_device()

    def fetch_mock_hardware(self) -> None:
        """Sets the internal pointer of device to the mock device.
        Sets it to None if the mock device is simulated to be killed.
        """
        self.device = self.mock_device if not self.mock_device.killed else None

    def setup_data(self):
        # Will still return a valid dictionary even if self.device is None
        self.data_source = DataSource(self.device)
        raise NotImplementedError("Must be implemented in subclasses.")

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
        if self.args_dict.get("hardware_mock", False):
            self.fetch_mock_hardware()
        else:
            self.fetch_hardware()  # This attempts to set `self.device` to a real device.
        # Determine if the device is considered 'alive'.
        device_alive = self.device is not None and (
            not isinstance(self.device, MockDevice) or not self.device.killed
        )
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
