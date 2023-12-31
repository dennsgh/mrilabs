import os
import time
from pathlib import Path

import pyvisa
from features.managers import DG4202Manager, EDUX1002AManager, StateManager
from header import DeviceName

from scheduler.timekeeper import Timekeeper
from scheduler.worker import Worker

DEVICE_LIST = [DeviceName.DG4202.value, DeviceName.EDUX1002A.value]

# DG4202_MOCK_DEVICE = DG4202Mock()
# ======================================================== #
# =======================File Paths======================= #
# ======================================================== #
STATE_FILE = Path(os.getenv("DATA"), "state.json")
FUNCTION_MAP_FILE = Path(os.getenv("DATA"), "registered_tasks.json")
TIMEKEEPER_JOBS_FILE = Path(os.getenv("DATA"), "jobs.json")
WORKER_LOGS = Path(os.getenv("LOGS"), "worker.log")
TIMEKEEPER_LOGS = Path(os.getenv("LOGS"), "worker.log")
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
app_start_time = time.time()
