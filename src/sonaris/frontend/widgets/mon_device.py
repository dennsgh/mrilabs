import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from PyQt6 import QtCore
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sonaris.defaults import MONITOR_FILE
from sonaris.frontend.managers.device import DeviceManager
from sonaris.utils import log as logutils

logger = logutils.get_logger()


class DeviceMonitorWidget(QWidget):
    def __init__(
        self,
        device_managers: Dict[str, DeviceManager],
        monitor_logs: Path = None,
        parent=None,
    ):
        super().__init__(parent)
        self.device_managers = device_managers  # Dictionary of device managers
        self.monitor_logs = monitor_logs or MONITOR_FILE
        self.device_statuses = {
            device_name: False for device_name in self.device_managers.keys()
        }
        self.initUI()
        self.setup_refresh_timer()
        self.load_event_log()

    def initUI(self):
        self.splitter = QSplitter(self)
        self.leftWidget = QWidget()
        self.leftLayout = QVBoxLayout(self.leftWidget)

        # Device Status Table
        self.status_table = QTableWidget(0, 2)  # Start with zero rows and two columns
        self.status_table.setHorizontalHeaderLabels(["Device Name", "Status"])
        # Make the table columns stretch to fit the space
        self.status_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.status_table.horizontalHeader().setStretchLastSection(True)

        self.leftLayout.addWidget(self.status_table)

        # Right Side Widget and Layout
        self.rightWidget = QWidget()
        self.rightLayout = QVBoxLayout(self.rightWidget)
        self.event_log_list = QListWidget()
        self.rightLayout.addWidget(self.event_log_list)

        self.splitter.addWidget(self.leftWidget)
        self.splitter.addWidget(self.rightWidget)

        # Clear List Button
        self.clear_list_button = QPushButton("Clear Event Log")
        self.clear_list_button.clicked.connect(self.clear_event_log)
        self.rightLayout.addWidget(self.clear_list_button)

        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.addWidget(self.splitter)

    def setup_refresh_timer(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_device_statuses)
        self.refresh_timer.start(1000)  # Refresh every 1 second

    def load_event_log(self):

        event_log = logutils.load_json_with_backup(self.monitor_logs)

        for event in event_log:
            self.event_log_list.addItem(
                f"[{event['timestamp']}] - {event['description']}"
            )

    def clear_event_log(self):
        # Confirmation message box
        reply = QMessageBox.question(
            self,
            "Clear Archive",
            "Are you sure you want to clear the monitoring logs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        # Check if the user confirmed the action
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.event_log_list.clear()
                with open(self.monitor_logs, "w") as file:
                    json.dump([], file, indent=4)
                QMessageBox.information(
                    self, "Success", "The monitoring logs has been cleared."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not clear the archive. {e}")

    def log_event(self, description: str):
        timestamp = datetime.now().isoformat()
        logger.info(f"[Monitor]: {description}")
        event = {"timestamp": timestamp, "description": description}
        if not self.monitor_logs.exists():
            with open(self.monitor_logs, "w") as file:
                json.dump([event], file, indent=4)
        else:
            with open(self.monitor_logs, "r+") as file:
                event_log = json.load(file)
                event_log.append(event)
                file.seek(0)
                json.dump(event_log, file, indent=4)
        self.event_log_list.addItem(f"[{timestamp}] - {description}")

    def update_device_statuses(self):
        self.status_table.setRowCount(len(self.device_managers))
        for row, (device_name, manager) in enumerate(self.device_managers.items()):
            self.update_device_status(device_name, manager, row)
 
    def update_device_status(self, device_name: str, manager: DeviceManager, row: int):
        try:
            is_alive = manager.is_device_alive()
            if is_alive and self.device_statuses[device_name] != is_alive:
                self.log_event(f"{device_name} Connected")
            elif not is_alive and self.device_statuses[device_name] != is_alive:
                self.log_event(f"{device_name} Disconnected")

            self.device_statuses[device_name] = is_alive
            status = "Connected" if is_alive else "Disconnected"

            # Create QTableWidgetItem instances for device name and status
            device_item = QTableWidgetItem(device_name)
            status_item = QTableWidgetItem(status)

            # Make the items non-editable
            device_item.setFlags(device_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            status_item.setFlags(status_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)

            # Set the items in the table
            self.status_table.setItem(row, 0, device_item)
            self.status_table.setItem(row, 1, status_item)
        except Exception as e:
            logger.error(f"Error updating device statuses: {e}")
