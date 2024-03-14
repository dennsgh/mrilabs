import pyvisa

from sonaris.device.data import DataBuffer

# Import classes and modules from sonaris.device module as needed.
from sonaris.device.edux1002a import EDUX1002A, EDUX1002ADataSource, EDUX1002AMock
from sonaris.defaults import OSCILLOSCOPE_BUFFER_SIZE
from sonaris.frontend.managers.device import DeviceManager
from sonaris.frontend.managers.state_manager import StateManager


class EDUX1002AManager(DeviceManager):
    device_type = EDUX1002A
    mock_device_type = EDUX1002AMock

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
