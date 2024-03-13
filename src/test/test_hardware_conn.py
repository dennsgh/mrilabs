import pytest
import pyvisa

from sonaris.device.device import DeviceDetector
from sonaris.device.dg4202 import DG4202, Interface

# @pytest.mark.hardware
# def test_DeviceDetector_detect_device():
#     rm = pyvisa.ResourceManager()
#     detected_device = DeviceDetector(
#         resource_manager=rm, device_type=DG4202
#     ).detect_device()

#     assert detected_device is not None
#     assert isinstance(detected_device.interface, Interface)
