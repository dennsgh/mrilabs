from PyQt6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

import sonaris.factory as factory
from sonaris.defaults import VERSION_STRING


class VersionWindow(QMessageBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Version Information")
        self.setText(f"Sonaris\nVersion: {VERSION_STRING}")  # Example version text
        self.setIcon(QMessageBox.Icon.Information)


class DeviceWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Device Information")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Check the connection status of the devices and create labels for them
        self.dg4202_status_label = QLabel("DG4202 Status: Checking...", self)
        layout.addWidget(self.dg4202_status_label)

        self.edux1002a_status_label = QLabel("EDUX1002A Status: Checking...", self)
        layout.addWidget(self.edux1002a_status_label)

        refresh_button = QPushButton("Refresh", self)
        refresh_button.clicked.connect(self.refresh_device_status)
        layout.addWidget(refresh_button)

        # Initial status check
        self.refresh_device_status()

    def refresh_device_status(self):
        # Refresh the status of the devices
        dg4202_status = (
            "Connected" if factory.dg4202_manager.get_device() else "Disconnected"
        )
        self.dg4202_status_label.setText(f"DG4202 Status: {dg4202_status}")

        edux1002a_status = (
            "Connected" if factory.edux1002a_manager.get_device() else "Disconnected"
        )
        self.edux1002a_status_label.setText(f"EDUX1002A Status: {edux1002a_status}")
