import os
from enum import Enum
from pathlib import Path

APP_NAME = "Sonaris"
VERSION_STRING = "v0.1.5"

GRAPH_RGB = (255, 255, 255)
OSCILLOSCOPE_BUFFER_SIZE = 512


class ErrorLevel(Enum):
    INFO = 0  # Missing parameters, etc.
    BAD_CONFIG = 1  # Missing tasks, etc.
    INVALID_YAML = 2  # Issues with loading/parsing YAML


class DeviceName(Enum):
    DG4202 = "DG4202"
    EDUX1002A = "EDUX1002A"


DEVICE_LIST = [DeviceName.DG4202.value, DeviceName.EDUX1002A.value]

DEFAULT_DATADIR = Path().home() / f".{APP_NAME.lower()}"
DEFAULT_DATADIR.mkdir(parents=True, exist_ok=True)

# Assuming DEFAULT_DATADIR is already a Path object
DEFAULT_DATADIR = Path(os.getenv("DATA")) if os.getenv("DATA") else DEFAULT_DATADIR
# Define file paths in one-liners, checking for existence and falling back to DEFAULT_DATADIR if necessary
STATE_FILE = (
    Path(DEFAULT_DATADIR / "state.json").exists()
    and Path(DEFAULT_DATADIR / "state.json")
    or (DEFAULT_DATADIR / "state.json")
)
TIMEKEEPER_JOBS_FILE = (
    Path(DEFAULT_DATADIR / "jobs.json").exists()
    and Path(DEFAULT_DATADIR / "jobs.json")
    or (DEFAULT_DATADIR / "jobs.json")
)
MONITOR_FILE = (
    Path(DEFAULT_DATADIR / "monitor.json").exists()
    and Path(DEFAULT_DATADIR / "monitor.json")
    or (DEFAULT_DATADIR / "monitor.json")
)
SETTINGS_FILE = (
    Path(DEFAULT_DATADIR / "settings.json").exists()
    and Path(DEFAULT_DATADIR / "settings.json")
    or (DEFAULT_DATADIR / "settings.json")
)
LOG_DIR = (
    Path(DEFAULT_DATADIR / "logs").exists()
    and Path(DEFAULT_DATADIR / "logs")
    or (DEFAULT_DATADIR / "logs")
)
LOG_DIR.mkdir(parents=True, exist_ok=True)
# UI CONFIG
TICK_INTERVAL = 500.0  # in ms
DECIMAL_POINTS = 5
NOT_FOUND_STRING = "Device not found!"
WAIT_KEYWORD = "wait"
TIMESTAMP_KEYWORD = "timestamp"
TASKS_MISSING = "No tasks available"
AT_TIME_KEYWORD = "at_time"
EXPERIMENT_KEYWORD = "experiment"
DELAY_KEYWORD = "delay"
# GRAFANA DEFAULTS
DEFAULT_TAB_STYLE = {"height": "30px", "padding": "2px"}
GF_SECURITY_ADMIN_PASSWORD = os.getenv("GF_SECURITY_ADMIN_PASSWORD", "admin")
GF_SECURITY_ADMIN_USER = os.getenv("GF_SECURITY_ADMIN_USER","admin")
GF_PORT = int(os.getenv("GF_PORT", "3000"))
# sonaris.defaults.py
GF_INSTALL_PLUGINS = "grafana-simple-json-datasource,yesoreyeram-infinity-datasource"


DATA_SOURCE_PORT = int(os.getenv("DATA_SOURCE_PORT", "5000"))
DATA_SOURCE_NAME = str(os.getenv("DATA_SOURCE_NAME", f"{APP_NAME}DataSource"))

GF_PROVISIONING_DIR = DEFAULT_DATADIR / "provisioning"

SONARIS_NETWORK_NAME = f"{APP_NAME.lower()}_network"
# GRAFANA DEFAULTS
