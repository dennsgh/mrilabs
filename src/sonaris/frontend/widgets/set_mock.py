from typing import Dict

from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sonaris.frontend.managers.device import DeviceManager
from sonaris.utils.log import get_logger

logger = get_logger()


class MockHardwareWidget(QWidget):
    def __init__(self, device_managers: Dict[str, DeviceManager], parent=None):
        super().__init__(parent)
        self.device_managers: Dict[str, DeviceManager] = device_managers
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.mock_settings = {}

        for device_name, manager in self.device_managers.items():
            row_layout = QHBoxLayout()

            label = QLabel(f"{device_name} Mock Kill:")
            row_layout.addWidget(label)

            dropdown = QComboBox()
            dropdown.addItem("False", False)  # Device is operational
            dropdown.addItem("True", True)  # Device is 'killed'
            dropdown.setCurrentIndex(manager.device.killed)

            row_layout.addWidget(dropdown)
            self.mock_settings[device_name] = dropdown

            layout.addLayout(row_layout)

        self.apply_button = QPushButton("Apply Mock Settings")
        self.apply_button.clicked.connect(self.apply_mock_settings)

        layout.addWidget(self.apply_button)
        self.setLayout(layout)

    def apply_mock_settings(self):
        for device_name, dropdown in self.mock_settings.items():
            mock_kill = dropdown.currentData()
            device_manager = self.device_managers[device_name]

            # Directly access mock_device and change its 'killed' state
            if device_manager.args_dict.get("hardware_mock"):
                logger.info(f"[Settings] {device_name} mock kill {mock_kill}")
                device_manager.set_mock_state(mock_kill)
