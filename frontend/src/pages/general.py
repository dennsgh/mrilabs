from typing import Callable

from features.managers import DG4202Manager, EDUX1002AManager
from header import TICK_INTERVAL
from PyQt6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget
from widgets.gen_oscilloscope import OscilloscopeWidget
from widgets.gen_signal import DG4202DefaultWidget
from widgets.templates import BasePage


class GeneralPage(BasePage):
    def __init__(
        self,
        dg4202_manager: DG4202Manager,
        edux1002a_manager: EDUX1002AManager,
        parent=None,
        args_dict: dict = None,
        root_callback: Callable = None,
    ):
        # Call the constructor of the BasePage class
        super().__init__(
            parent=parent, args_dict=args_dict, root_callback=root_callback
        )

        # Initialize GeneralPage-specific attributes
        self.dg4202_manager = dg4202_manager
        self.edux1002a_manager = edux1002a_manager

        self.initUI()

    def check_connection(self) -> bool:
        return self.dg4202_manager.is_device_alive()

    def initUI(self):
        self.main_layout = QVBoxLayout()
        self.oscilloscope = OscilloscopeWidget(
            self.edux1002a_manager, tick=TICK_INTERVAL
        )
        self.main_layout.addWidget(self.oscilloscope)
        self.status_label = QLabel("")
        self.main_layout.addWidget(self.status_label)

        self.default_widget = DG4202DefaultWidget(
            self.dg4202_manager, self, self.args_dict
        )
        self.main_layout.addWidget(self.default_widget)

        self.setLayout(self.main_layout)

    def update(self):
        if self.check_connection():
            self.default_widget.update()
