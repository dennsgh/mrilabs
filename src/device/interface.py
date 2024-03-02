import abc
from datetime import datetime
from typing import Optional

import pyvisa


class Interface(abc.ABC):

    def __init__(self, resource: pyvisa.Resource, address: Optional[str] = None):
        self.inst = resource
        self.address = address
        self.debug = False

    @abc.abstractmethod
    def write(self, command: str) -> None:
        """
        Abstract method for writing a command to the interface.

        Args:
            command (str): The command to be written.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def read(self, command: str) -> str:
        """
        Abstract method for reading a response from the interface.

        Args:
            command (str): The command to be sent for reading.

        Returns:
            str: The response received from the interface.
        """
        raise NotImplementedError


class EthernetInterface(Interface):

    def __init__(self, resource: pyvisa.Resource):
        self.ip_address = resource.resource_name.split("::")[1]
        super().__init__(resource, address=self.ip_address)

    def write(self, command: str) -> None:
        self.inst.write(command)
        if self.debug:
            print(f"[{datetime.now()}]{command}")

    def read(self, command: str) -> str:
        if self.debug:
            print(f"[{datetime.now()}]{command}")
        return self.inst.query(command)


class USBInterface(Interface):

    def __init__(self, resource: pyvisa.Resource):
        self.usb_address = resource
        super().__init__(resource, address=self.usb_address)

    def write(self, command: str) -> None:
        self.inst.write(command)
        if self.debug:
            print(f"[{datetime.now()}]{command}")

    def read(self, command: str) -> str:
        if self.debug:
            print(f"[{datetime.now()}]{command}")
        return self.inst.query(command)
