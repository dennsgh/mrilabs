import os
from pathlib import Path
from typing import Callable, Dict

from PyQt6.QtWidgets import QVBoxLayout

from sonaris.frontend.managers.device import DeviceManager
from sonaris.frontend.widgets.set_mock import MockHardwareWidget
from sonaris.frontend.widgets.set_state import SettingsStateWidget
from sonaris.frontend.widgets.templates import BasePage
from sonaris.defaults import SETTINGS_FILE

class SettingsPage(BasePage):
    PAGE_NAME = "Settings"

    def __init__(
        self,
        device_managers: Dict[str, DeviceManager] = None,
        parent=None,
        args_dict: dict = None,
        root_callback: Callable = None,
    ):
        super().__init__(
            parent=parent, args_dict=args_dict, root_callback=root_callback
        )
        self.device_managers = device_managers
        self.settings_widget = SettingsStateWidget(
            settings_file=SETTINGS_FILE
        )
        self.mock_hardware_widget = None  # Will be initialized if hardware_mock is True
        self.initUI()
        self.setLayout(self.main_layout)

    def initUI(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.settings_widget)

        # Add the mock hardware settings widget if hardware_mock is True
        if self.args_dict and self.args_dict.get("hardware_mock"):
            self.mock_hardware_widget = MockHardwareWidget(self.device_managers)
            self.main_layout.addWidget(self.mock_hardware_widget)

    def update(self):
        pass  # Implement any update logic here if needed
