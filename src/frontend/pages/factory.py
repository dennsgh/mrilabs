import os
import time
from pathlib import Path

import pyvisa

from frontend.managers.dg4202 import DG4202Manager
from frontend.managers.edux1002a import EDUX1002AManager
from frontend.managers.state_manager import StateManager
from scheduler.timekeeper import Timekeeper
from scheduler.worker import Worker

# ======================================================== #
# =======================File Paths======================= #
# ======================================================== #
STATE_FILE = Path(os.getenv("DATA"), "state.json")
FUNCTION_MAP_FILE = Path(os.getenv("DATA"), "registered_tasks.json")
TIMEKEEPER_JOBS_FILE = Path(os.getenv("DATA"), "jobs.json")
MONITOR_FILE = Path(os.getenv("DATA"), "monitor.json")
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
