from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from widgets.templates import ModuleWidget
from device.dg4202 import DG4202
from pages import plotter
from datetime import datetime, timedelta
import pyqtgraph as pg
from features.managers import DG4202Manager
from widgets.dg_default import DG4202DefaultWidget
from widgets.dg_experiment import DG4202ExperimentWidget

NOT_FOUND_STRING = 'Device not found!'
TIMER_INTERVAL = 1000.  # in ms
TIMER_INTERVAL_S = TIMER_INTERVAL / 1000.  # in ms

DEFAULT_TAB_STYLE = {'height': '30px', 'padding': '2px'}


class GeneralPage(ModuleWidget):

    def check_connection(self) -> bool:
        self.my_generator = self.dg4202_manager.get_device()
        self.all_parameters = self.dg4202_manager.data_source.query_data()
        if self.my_generator is not None:
            is_alive = self.my_generator.is_connection_alive()
            if not is_alive:
                self.my_generator = None
            return is_alive
        return False

    def __init__(self, dg4202_manager: DG4202Manager, parent=None, args_dict: dict = None):
        super().__init__(parent=parent)
        self.dg4202_manager = dg4202_manager
        self.args_dict = args_dict
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout()
        self.check_connection()
        self.connection_status_label = QLabel(
            f"Connection Status: {self.all_parameters.get('connected', 'Not connected')}")
        self.main_layout.addWidget(self.connection_status_label)

        self.status_label = QLabel("")
        self.main_layout.addWidget(self.status_label)

        # Create the tab widget
        self.tab_widget = QTabWidget()

        # Default Widget Tab
        self.default_widget = DG4202DefaultWidget(self.dg4202_manager, self, self.args_dict)
        self.tab_widget.addTab(self.default_widget, "Default Mode")

        # Adding the tab widget to the main layout
        self.main_layout.addWidget(self.tab_widget)

        self.setLayout(self.main_layout)