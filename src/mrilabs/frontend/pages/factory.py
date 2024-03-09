import os
import time
from pathlib import Path

import pyvisa

from mrilabs.frontend.header import DEFAULT_WORKDIR
from mrilabs.frontend.managers.dg4202 import DG4202Manager
from mrilabs.frontend.managers.edux1002a import EDUX1002AManager
from mrilabs.frontend.managers.state_manager import StateManager
from mrilabs.scheduler.timekeeper import Timekeeper
from mrilabs.scheduler.worker import Worker

# ======================================================== #
# =======================File Paths======================= #
# ======================================================== #
# Ensure DATA has a default value if not set; here we use DEFAULT_WORKDIR as a fallback

# Assuming DEFAULT_WORKDIR is already a Path object
data_dir = Path(os.getenv("DATA")) if os.getenv("DATA") else DEFAULT_WORKDIR
# Define file paths in one-liners, checking for existence and falling back to DEFAULT_WORKDIR if necessary
STATE_FILE = (
    Path(data_dir / "state.json").exists()
    and Path(data_dir / "state.json")
    or (DEFAULT_WORKDIR / "state.json")
)
FUNCTION_MAP_FILE = (
    Path(data_dir / "registered_tasks.json").exists()
    and Path(data_dir / "registered_tasks.json")
    or (DEFAULT_WORKDIR / "registered_tasks.json")
)
TIMEKEEPER_JOBS_FILE = (
    Path(data_dir / "jobs.json").exists()
    and Path(data_dir / "jobs.json")
    or (DEFAULT_WORKDIR / "jobs.json")
)
MONITOR_FILE = (
    Path(data_dir / "monitor.json").exists()
    and Path(data_dir / "monitor.json")
    or (DEFAULT_WORKDIR / "monitor.json")
)
# ======================================================== #
# Place holder globals, these are initialized in app.py
# ======================================================== #
resource_manager: pyvisa.ResourceManager = None
state_manager: StateManager = None
dg4202_manager: DG4202Manager = None
edux1002a_manager: EDUX1002AManager = None
# ======================================================== #
# ===================Worker Modules======================= #
# ======================================================== #
worker: Worker = None
timekeeper: Timekeeper = None
