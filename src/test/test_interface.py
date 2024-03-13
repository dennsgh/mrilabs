from unittest.mock import Mock, patch

from sonaris.device.device import Device, DeviceDetector
from sonaris.device.interface import EthernetInterface, USBInterface


class GenericDevice(Device):
    IDN_STRING = "Generic Device ID"


@patch("pyvisa.ResourceManager", return_value=Mock())
def test_detect_device_with_tcpip_resource(mock_resource_manager):
    mock_rm = mock_resource_manager.return_value
    mock_device = Mock()

    # Correctly set up the resource_name attribute on the mock_device
    mock_device.resource_name = "TCPIP0::192.168.1.100::INSTR"
    mock_device.query.return_value = "Manufacturer,Generic Device ID,Serial,Version"

    # Simulate a device resource list that includes a TCPIP resource
    mock_rm.list_resources.return_value = [mock_device.resource_name]
    mock_rm.open_resource.return_value = mock_device

    detector = DeviceDetector(mock_rm, GenericDevice)
    result = detector.detect_device()

    # Ensure the result is an instance of GenericDevice with an EthernetInterface
    assert isinstance(result, GenericDevice)
    assert isinstance(result.interface, EthernetInterface)


@patch("pyvisa.ResourceManager", return_value=Mock())
def test_detect_device_with_usb_resource(mock_resource_manager):
    mock_rm = mock_resource_manager.return_value
    mock_device = Mock()
    mock_device.query.return_value = "Manufacturer,Generic Device ID,Serial,Version"

    # Simulate a device resource list that includes a USB resource
    mock_rm.list_resources.return_value = ["USB0::0x1234::0x5678::SN12345::0::INSTR"]
    mock_rm.open_resource.return_value = mock_device

    detector = DeviceDetector(mock_rm, GenericDevice)
    result = detector.detect_device()

    # Ensure the result is an instance of GenericDevice with a USBInterface
    assert isinstance(result, GenericDevice)
    assert isinstance(result.interface, USBInterface)


@patch("pyvisa.ResourceManager", return_value=Mock())
def test_detect_device_with_no_device(mock_resource_manager):
    mock_rm = mock_resource_manager.return_value
    # Simulate an empty resource list (i.e., no devices detected)
    mock_rm.list_resources.return_value = []

    detector = DeviceDetector(mock_rm, GenericDevice)
    result = detector.detect_device()

    # Ensure that the detection result is None when no devices are found
    assert result is None
