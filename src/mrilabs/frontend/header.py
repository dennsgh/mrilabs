import os
from enum import Enum
from pathlib import Path

VERSION_STRING = "v0.1.1"

GRAPH_RGB = (255, 255, 255)
OSCILLOSCOPE_BUFFER_SIZE = 512


class ErrorLevel(Enum):
    INFO = 0  # Missing parameters, etc.
    BAD_CONFIG = 1  # Missing tasks, etc.
    INVALID_YAML = 2  # Issues with loading/parsing YAML


class DeviceName(Enum):
    DG4202 = "DG4202"
    EDUX1002A = "EDUX1002A"


DEFAULT_DATADIR = Path().home() / ".mrilabs"
DEFAULT_DATADIR.mkdir(parents=True, exist_ok=True)

# Assuming DEFAULT_DATADIR is already a Path object
data_dir = Path(os.getenv("DATA")) if os.getenv("DATA") else DEFAULT_DATADIR
# Define file paths in one-liners, checking for existence and falling back to DEFAULT_DATADIR if necessary
STATE_FILE = (
    Path(data_dir / "state.json").exists()
    and Path(data_dir / "state.json")
    or (DEFAULT_DATADIR / "state.json")
)
TIMEKEEPER_JOBS_FILE = (
    Path(data_dir / "jobs.json").exists()
    and Path(data_dir / "jobs.json")
    or (DEFAULT_DATADIR / "jobs.json")
)
MONITOR_FILE = (
    Path(data_dir / "monitor.json").exists()
    and Path(data_dir / "monitor.json")
    or (DEFAULT_DATADIR / "monitor.json")
)
SETTINGS_FILE = (
    Path(data_dir / "settings.json").exists()
    and Path(data_dir / "settings.json")
    or (DEFAULT_DATADIR / "settings.json")
)
LOG_FILE = (
    Path(data_dir / "mrilabs.log").exists()
    and Path(data_dir / "mrilabs.log")
    or (DEFAULT_DATADIR / "mrilabs.log")
)

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
