import os
from pathlib import Path
from typing import Callable, Dict

from features.managers import DeviceManagerBase
from PyQt6.QtWidgets import QVBoxLayout
from widgets.mock_settings import MockHardwareWidget
from widgets.settings_state import SettingsStateWidget
from widgets.templates import BasePage


class SettingsPage(BasePage):
    def __init__(
        self,
        device_managers: Dict[str, DeviceManagerBase] = None,
        parent=None,
        args_dict: dict = None,
        root_callback: Callable = None,
    ):
        super().__init__(
            parent=parent, args_dict=args_dict, root_callback=root_callback
        )
        self.device_managers = device_managers
        self.settings_widget = SettingsStateWidget(
            settings_file=Path(os.getenv("DATA"), "settings.json")
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
