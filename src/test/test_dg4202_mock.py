import pytest

from sonaris.device.dg4202 import DG4202Mock


@pytest.fixture
def mock_device():
    return DG4202Mock()


def test_killed_state(mock_device: DG4202Mock):
    # Initially, the connection should be alive
    assert mock_device.is_connection_alive() is True

    # Simulate device kill
    mock_device.simulate_kill(True)
    assert mock_device.is_connection_alive() is False

    # Ensure operations are blocked in killed state
    with pytest.raises(Exception, match="Device DG4202Mock is disconnected!"):
        mock_device.set_waveform(channel=1, waveform_type="SIN")


def test_device_disconnected_behavior():
    device = DG4202Mock()
    device.simulate_kill(True)  # Simulate device disconnection

    # Verify that operations are blocked and raise the expected exception
    with pytest.raises(Exception, match="Device DG4202Mock is disconnected!"):
        device.set_waveform(channel=1, waveform_type="SIN")


def test_state_change_on_write(mock_device: DG4202Mock):
    # Test setting output on for channel 1
    mock_device.simulate_kill(False)
    mock_device.set_waveform(channel=1, waveform_type="SIN")
    assert mock_device.interface.state["SOURce1:FUNCtion"] == "SIN"

    # Change waveform type and verify state update
    mock_device.set_waveform(channel=1, waveform_type="SQUARE")
    assert mock_device.interface.state["SOURce1:FUNCtion"] == "SQUARE"


def test_read_operations(mock_device: DG4202Mock):
    # Directly manipulate the state for testing read operations
    mock_device.interface.state["SOURce1:FUNCtion"] = "RAMP"

    # Verify that the read method returns the expected value
    assert mock_device.interface.read("SOURce1:FUNCtion?") == "RAMP"
