import re
from typing import Optional, Type

import pyvisa

from sonaris.device.interface import EthernetInterface, Interface, USBInterface


class Device:
    IDN_STRING = "Generic Device ID string"

    def __init__(self, interface: Interface):
        self.interface = interface

    def is_connection_alive(self) -> bool:
        raise NotImplementedError(
            "This class has to be implemented and used as a base class!"
        )


class MockDevice(Device):
    def __init__(self, interface: Interface):
        self.killed = False
        self.blocked_methods = (
            set()
        )  # Default empty set, to be overridden by child classes
        super().__init__(interface)

    def simulate_kill(self, kill: bool):
        self.killed = kill

    def is_connection_alive(self) -> bool:
        return not self.killed

    def __getattribute__(self, name):
        if object.__getattribute__(self, "killed") and name in object.__getattribute__(
            self, "blocked_methods"
        ):
            raise Exception(f"Device {self.__class__.__name__} is disconnected!")
        else:
            return object.__getattribute__(self, name)


class DeviceDetector:
    def __init__(
        self,
        resource_manager: pyvisa.ResourceManager,
        device_type: Type[Device],
    ):
        self.rm = resource_manager
        self.device_type = device_type

    def detect_device(self) -> Optional[Device]:
        """
        Method that attempts to detect a device connected via TCP/IP or USB.
        Loops through all available resources, attempting to open each one and query its identity.
        If the device is found, it creates and returns a DG4202 instance.

        Returns:
            A device object with the interface attached to it.
        """
        resources = self.rm.list_resources()

        for resource in resources:
            if re.match("^TCPIP", resource):
                try:
                    device = self.rm.open_resource(resource)
                    idn = device.query("*IDN?")
                    if self.device_type.IDN_STRING in idn:
                        return self.device_type(EthernetInterface(device))
                except pyvisa.errors.VisaIOError:
                    pass
            elif re.match("^USB", resource):
                try:
                    device = self.rm.open_resource(resource)
                    idn = device.query("*IDN?")
                    if self.device_type.IDN_STRING in idn:
                        return self.device_type(USBInterface(device))
                except pyvisa.errors.VisaIOError:
                    pass

        return None
