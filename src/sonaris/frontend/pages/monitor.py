from pathlib import Path
from typing import Callable

from PyQt6.QtWidgets import QVBoxLayout

from sonaris.frontend.widgets.mon_device import (  # Assuming this is the path
    DeviceMonitorWidget,
)
from sonaris.frontend.widgets.templates import BasePage


class MonitorPage(BasePage):
    PAGE_NAME = "Monitor"

    def __init__(
        self,
        device_managers: dict,
        parent=None,
        args_dict: dict = None,
        monitor_logs: Path = None,
        root_callback: Callable = None,
    ):
        super().__init__(
            parent=parent, args_dict=args_dict, root_callback=root_callback
        )
        self.device_managers = device_managers
        self.monitor_logs = monitor_logs
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout()
        self.device_monitor_widget = DeviceMonitorWidget(
            self.device_managers, monitor_logs=self.monitor_logs
        )
        self.main_layout.addWidget(self.device_monitor_widget)
        self.setLayout(self.main_layout)

    def update(self):
        # Implement any necessary updates when the page is loaded or refreshed
        pass
