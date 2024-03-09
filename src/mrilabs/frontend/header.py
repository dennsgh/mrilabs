from enum import Enum
from pathlib import Path

VERSION_STRING = "v0.1.0"

GRAPH_RGB = (255, 255, 255)
OSCILLOSCOPE_BUFFER_SIZE = 512


class ErrorLevel(Enum):
    INFO = 0  # Missing parameters, etc.
    BAD_CONFIG = 1  # Missing tasks, etc.
    INVALID_YAML = 2  # Issues with loading/parsing YAML


class DeviceName(Enum):
    DG4202 = "DG4202"
    EDUX1002A = "EDUX1002A"


DEFAULT_WORKDIR = Path().home() / ".mrilabs"
DEFAULT_WORKDIR.mkdir(parents=True, exist_ok=True)
DECIMAL_POINTS = 5
DEVICE_LIST = [DeviceName.DG4202.value, DeviceName.EDUX1002A.value]
NOT_FOUND_STRING = "Device not found!"
WAIT_KEYWORD = "wait"
TIMESTAMP_KEYWORD = "timestamp"
TASKS_MISSING = "No tasks available"
AT_TIME_KEYWORD = "at_time"
EXPERIMENT_KEYWORD = "experiment"
DELAY_KEYWORD = "delay"
TICK_INTERVAL = 500.0  # in ms

DEFAULT_TAB_STYLE = {"height": "30px", "padding": "2px"}
