import abc
from datetime import datetime
from typing import Optional

import pyvisa


class Interface(abc.ABC):

    def __init__(self, resource: pyvisa.Resource, address: Optional[str] = None):
        self.inst = resource
        self.address = address
        self.debug = False

    def write(self, command: str) -> None:
        self.inst.write(command)
        if self.debug:
            print(f"[{datetime.now()}]{command}")

    def read(self, command: str) -> str:
        if self.debug:
            print(f"[{datetime.now()}]{command}")
        return self.inst.query(command)


class EthernetInterface(Interface):
    def __init__(self, resource: pyvisa.Resource):
        # set address
        super().__init__(resource, address=resource.resource_name.split("::")[1])


class USBInterface(Interface):
    def __init__(self, resource: pyvisa.Resource):
        # subject to future change, unsure if resource is supposed to be address as well
        super().__init__(resource, address=resource.resource_name)
