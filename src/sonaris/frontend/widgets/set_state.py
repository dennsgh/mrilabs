import json
from pathlib import Path

from PyQt6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from sonaris.defaults import VERSION_STRING


class SettingsStateWidget(QWidget):
    def __init__(self, settings_file: Path, parent=None):
        super().__init__(parent)
        self.settings_file = settings_file
        self.load_settings()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Add a label and edit for a sample setting
        self.setting_label = QLabel(f"Sonaris {VERSION_STRING}")
        # self.setting_edit = QLineEdit(self)
        # self.setting_edit.setText(self.settings.get("sample_setting", ""))

        # Create buttons
        # self.apply_button = QPushButton("Apply")
        # self.apply_button.clicked.connect(self.apply_settings)

        # self.reset_button = QPushButton("Reset")
        # self.reset_button.clicked.connect(self.reset_settings)

        # Arrange widgets in the layout
        layout.addWidget(self.setting_label)
        # layout.addWidget(self.setting_edit)
        # layout.addWidget(self.apply_button)
        # layout.addWidget(self.reset_button)

        self.setLayout(layout)

    def load_settings(self):
        try:
            with open(self.settings_file, "r") as f:
                self.settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = {}

    def save_settings(self):
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)

    def apply_settings(self):
        # Save the current state of the settings
        self.settings["sample_setting"] = self.setting_edit.text()
        self.save_settings()

    def reset_settings(self):
        # Reset the settings to their saved state
        self.load_settings()
        self.setting_edit.setText(self.settings.get("sample_setting", ""))
