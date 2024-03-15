import pyvisa

from sonaris.frontend.managers.dg4202 import DG4202Manager
from sonaris.frontend.managers.edux1002a import EDUX1002AManager
from sonaris.frontend.managers.state_manager import StateManager
from sonaris.scheduler.timekeeper import Timekeeper
from sonaris.scheduler.worker import Worker
from sonaris.services.datasource import DataSourceService
from sonaris.services.grafana import GrafanaService
# ======================================================== #
# Place holder globals, these are initialized in app.py
# ======================================================== #
resource_manager: pyvisa.ResourceManager = None
state_manager: StateManager = None
dg4202_manager: DG4202Manager = None
edux1002a_manager: EDUX1002AManager = None
# ======================================================== #
# ====================Worker Modules====================== #
# ======================================================== #
worker: Worker = None
timekeeper: Timekeeper = None
# ======================================================== #
# ======================Services========================== #
# ======================================================== #
grafana_service: GrafanaService = None
datasource_service: DataSourceService = None