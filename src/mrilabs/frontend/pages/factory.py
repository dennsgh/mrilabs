import os
import time
from pathlib import Path

import pyvisa

from mrilabs.frontend.managers.dg4202 import DG4202Manager
from mrilabs.frontend.managers.edux1002a import EDUX1002AManager
from mrilabs.frontend.managers.state_manager import StateManager
from mrilabs.scheduler.timekeeper import Timekeeper
from mrilabs.scheduler.worker import Worker

# ======================================================== #
# =======================File Paths======================= #
# ======================================================== #
# Ensure DATA has a default value if not set; here we use DEFAULT_WORKDIR as a fallback

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
