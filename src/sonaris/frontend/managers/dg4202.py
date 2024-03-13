import pyvisa

# Import classes and modules from sonaris.device module as needed.
from sonaris.device.dg4202 import DG4202, DG4202DataSource, DG4202Mock
from sonaris.frontend.managers.device import DeviceManager
from sonaris.frontend.managers.state_manager import StateManager


class DG4202Manager(DeviceManager):
    device_type = DG4202
    mock_device_type = DG4202Mock

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
