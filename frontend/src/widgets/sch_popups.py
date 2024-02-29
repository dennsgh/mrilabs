from datetime import datetime, timedelta
from typing import Callable

import yaml
from features.task_validator import get_task_enum_name, get_task_enum_value, is_in_enum
from features.tasks import TaskName, get_tasks
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from widgets.sch_experiments import ExperimentConfiguration
from widgets.sch_parameters import ParameterConfiguration

from scheduler.timekeeper import Timekeeper


class JobConfigPopup(QDialog):
    TIMESTAMP = "timestamp"
    DURATION = "duration"
    NO_TASK_STRING = "No tasks available"

    def __init__(self, timekeeper: Timekeeper, callback: Callable):
        super().__init__()
        self.resize(800, 320)
        self.task_dict = get_tasks(flatten=False)
        self.task_enum = TaskName
        self.timekeeper = timekeeper
        self.callback = callback

        self.initUI()
        self.connectSignals()
        self.updateTaskList()

    def initUI(self):
        self.gridLayout = QGridLayout(self)
        self.setupConfigurationGroup()
        self.setupTimeConfigurationGroup()
        self.setupParameterConfigurationGroup()
        self.setupActionButtons()
        self.setupYamlDisplayWidget()

    def setupConfigurationGroup(self):
        configurationGroup = QGroupBox("Configuration")
        configurationLayout = QVBoxLayout(configurationGroup)
        self.deviceSelect = QComboBox()
        self.taskSelect = QComboBox()

        configurationLayout.addWidget(QLabel("Select Device:"))
        configurationLayout.addWidget(self.deviceSelect)
        configurationLayout.addWidget(QLabel("Select Task:"))
        configurationLayout.addWidget(self.taskSelect)

        self.deviceSelect.addItems(self.task_dict.keys())
        self.gridLayout.addWidget(configurationGroup, 0, 0, 1, 2)

    def setupTimeConfigurationGroup(self):
        timeConfigGroup = QGroupBox()
        timeConfigLayout = QHBoxLayout(timeConfigGroup)
        self.timeConfigComboBox = QComboBox()
        self.timeConfigComboBox.addItems([self.DURATION, self.TIMESTAMP])
        timeConfigLayout.addWidget(self.timeConfigComboBox)

        self.setupTimeConfiguration(timeConfigLayout)
        self.gridLayout.addWidget(timeConfigGroup, 1, 0)

    def setupParameterConfigurationGroup(self):
        self.parameterConfig = ParameterConfiguration(
            task_dictionary=self.task_dict,
            parent=self,
            task_enum=self.task_enum,
            input_callback=self.updateYamlDisplay,
        )
        parameterConfigGroup = QGroupBox("Parameter Configuration")
        parameterConfigLayout = QVBoxLayout(parameterConfigGroup)
        parameterConfigLayout.addWidget(self.parameterConfig)
        self.gridLayout.addWidget(parameterConfigGroup, 1, 1)

    def setupActionButtons(self):
        buttonsLayout = QHBoxLayout()
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        buttonsLayout.addWidget(self.okButton)
        buttonsLayout.addWidget(self.cancelButton)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        self.gridLayout.addLayout(buttonsLayout, 2, 0, 1, 2)

    def setupYamlDisplayWidget(self):
        self.yamlDisplayWidget = QTextEdit()
        self.yamlDisplayWidget.setReadOnly(True)
        self.gridLayout.addWidget(self.yamlDisplayWidget, 0, 2, 2, 2)  #

    def connectSignals(self):
        self.deviceSelect.currentIndexChanged.connect(self.updateTaskList)
        self.taskSelect.currentIndexChanged.connect(self.updateUI)
        self.timeConfigComboBox.currentIndexChanged.connect(self.updateYamlDisplay)

    def updateYamlDisplay(self):
        # This method updates the YAML display based on current configurations
        parameters = self.parameterConfig.getConfiguration()
        now = datetime.now()

        if self.timeConfigComboBox.currentText() == self.TIMESTAMP:
            schedule_time = self.getDateTimeFromInputs()
            # Calculate the duration as the difference between the schedule time and now
            duration = schedule_time - now
        else:
            # Directly use the duration from the inputs if "Duration" is selected
            duration = self.getDateTimeFromInputs() - now

        # Ensure duration is always positive before displaying
        if duration.total_seconds() < 0:
            duration = timedelta(seconds=0)  # Reset to 0 if negative

        config = {
            "experiment": {
                "steps": [
                    {
                        "task": get_task_enum_name(
                            self.taskSelect.currentText(), TaskName
                        ),
                        "duration": duration.total_seconds(),
                        "parameters": parameters,
                    }
                ]
            }
        }
        yamlStr = yaml.dump(config, sort_keys=False, default_flow_style=False)
        self.yamlDisplayWidget.setText(yamlStr)

    def updateTimeConfigurationVisibility(self, selection):
        isTimestamp = selection == self.TIMESTAMP
        self.timestampWidget.setVisible(isTimestamp)
        self.durationWidget.setVisible(not isTimestamp)

    def updateTaskList(self):
        selected_device = self.deviceSelect.currentText()
        tasks = self.task_dict.get(selected_device, {}).keys()
        self.taskSelect.clear()
        if tasks:
            self.taskSelect.addItems(tasks)
            self.taskSelect.setCurrentIndex(0)
        else:
            self.taskSelect.addItem(self.NO_TASK_STRING)
            self.taskSelect.setCurrentIndex(0)
        self.updateUI()

    def updateUI(self):
        selected_device = self.deviceSelect.currentText()
        selected_task = self.taskSelect.currentText()
        # Check if the selected task is valid before updating UI
        if selected_task and selected_task != "No tasks available":
            self.parameterConfig.updateUI(selected_device, selected_task)
            self.updateYamlDisplay()

        else:
            pass

    def setupTimeConfiguration(self, layout):
        # Create widgets to hold the grid layouts
        self.durationWidget = QWidget(self)
        self.timestampWidget = QWidget(self)

        # Set grid layouts to these widgets
        timestampGridLayout = self.createDateTimeInputs(datetime.now())
        durationGridLayout = self.createDurationInputs()
        self.timestampWidget.setLayout(timestampGridLayout)
        self.durationWidget.setLayout(durationGridLayout)

        # Add these widgets to the main layout
        layout.addWidget(self.timestampWidget)
        layout.addWidget(self.durationWidget)

        self.updateTimeConfigurationVisibility(self.timeConfigComboBox.currentText())

        # Connect the combobox signal
        self.timeConfigComboBox.currentIndexChanged.connect(
            lambda: self.updateTimeConfigurationVisibility(
                self.timeConfigComboBox.currentText()
            )
        )

    def createDateTimeInputs(self, default_value):
        gridLayout = QGridLayout()
        self.timestampInputs = {}

        # Define the fields, limits, and their positions in the grid
        fields = [
            ("Year", "year", 0, 0, 1900, 2100),
            ("Month", "month", 1, 0, 1, 12),
            ("Day", "day", 2, 0, 1, 31),
            ("Hour", "hour", 0, 1, 0, 23),
            ("Minute", "minute", 1, 1, 0, 59),
            ("Second", "second", 2, 1, 0, 59),
            # Assuming milliseconds need to be input as a float
            ("Millisecond", "millisecond", 3, 1, 0, 999),
        ]

        for label_text, field, row, col, min_val, max_val in fields:
            label = QLabel(f"{label_text}:")
            if field == "millisecond":
                inputWidget = QDoubleSpinBox(self)
                inputWidget.setDecimals(0)  # Adjust as needed for precision
            else:
                inputWidget = QSpinBox(self)

            inputWidget.setRange(min_val, max_val)
            inputWidget.setValue(getattr(default_value, field, min_val))
            inputWidget.valueChanged.connect(self.updateYamlDisplay)

            gridLayout.addWidget(label, row, col * 2)
            gridLayout.addWidget(inputWidget, row, col * 2 + 1)
            self.timestampInputs[field] = inputWidget

        return gridLayout

    def createDurationInputs(self):
        gridLayout = QGridLayout()
        self.durationInputs = {}

        # Define the fields and their positions in the grid
        fields = [
            ("Days", "days", 0, 0, 0, 9999),
            ("Hours", "hours", 0, 1, 0, 23),
            ("Minutes", "minutes", 1, 1, 0, 59),
            ("Seconds", "seconds", 2, 1, 0, 59),
            ("Milliseconds", "milliseconds", 3, 1, 0, 999),
        ]

        for label_text, field, row, col, min_val, max_val in fields:
            label = QLabel(f"{label_text}:")
            if field == "millisecond":
                inputWidget = QDoubleSpinBox(self)
                inputWidget.setDecimals(0)  # Adjust as needed for precision
            else:
                inputWidget = QSpinBox(self)

            inputWidget.setRange(min_val, max_val)
            inputWidget.setValue(min_val)
            inputWidget.valueChanged.connect(self.updateYamlDisplay)

            gridLayout.addWidget(label, row, col * 2)
            gridLayout.addWidget(inputWidget, row, col * 2 + 1)
            self.durationInputs[field] = inputWidget

        return gridLayout

    def toggleTimeInputs(self):
        # Toggle visibility of time input fields based on selected option
        isTimestamp = bool(self.timeConfigComboBox.currentText() == self.TIMESTAMP)
        for input in self.timestampInputs:
            input.setVisible(isTimestamp)
        for input in self.durationInputs:
            input.setVisible(not isTimestamp)

    def accept(self):
        # Schedule the task with either timestamp or duration
        selected_task = self.taskSelect.currentText()
        schedule_time = self.getDateTimeFromInputs()
        try:
            # Get parameters from ParameterConfiguration
            params = self.parameterConfig.getConfiguration()

            self.timekeeper.add_job(
                task_name=selected_task, schedule_time=schedule_time, kwargs=params
            )
            # Callback to update the UI, etc.
            self.callback()
            super().accept()
        except Exception as e:
            print({f"Error during commissioning job on : {e}"})

    def getDateTimeFromInputs(self):
        if self.timeConfigComboBox.currentText() == self.TIMESTAMP:
            # Convert microsecond value to an integer
            microsecond = int(self.timestampInputs["millisecond"].value() * 1000)

            return datetime(
                year=self.timestampInputs["year"].value(),
                month=self.timestampInputs["month"].value(),
                day=self.timestampInputs["day"].value(),
                hour=self.timestampInputs["hour"].value(),
                minute=self.timestampInputs["minute"].value(),
                second=self.timestampInputs["second"].value(),
                microsecond=microsecond,
            )
        else:
            duration = timedelta(
                days=self.durationInputs["days"].value(),
                hours=self.durationInputs["hours"].value(),
                minutes=self.durationInputs["minutes"].value(),
                seconds=self.durationInputs["seconds"].value(),
                milliseconds=int(
                    self.durationInputs["milliseconds"].value()
                ),  # Ensure integer for milliseconds
            )
            return datetime.now() + duration


class ExperimentConfigPopup(QDialog):
    def __init__(self, timekeeper: Timekeeper, callback: Callable, parent=None):
        super().__init__(parent)
        self.timekeeper = timekeeper
        self.callback = callback
        self.task_dict = get_tasks(flatten=True)
        self.task_enum = TaskName
        self.experiment_config = ExperimentConfiguration(
            self, self.task_dict, self.task_enum
        )
        self.initUI()
        self.showDefaultMessage()

    def merge_parameters(self, parameter_list):
        merged_parameters = {}
        for parameter_dict in parameter_list:
            merged_parameters.update(parameter_dict)
        return merged_parameters

    def initUI(self):
        self.setWindowTitle("Experiment Configuration")
        self.resize(600, 500)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout = QVBoxLayout(self)

        # Use a QStackedWidget to switch between default message and loaded configuration UI
        self.parametersStack = QStackedWidget(self)
        self.layout.addWidget(self.parametersStack)
        self.parametersStack.addWidget(
            self.experiment_config
        )  # Add experiment configuration UI

        self.loadConfigButton = QPushButton("Load Configuration", self)
        self.loadConfigButton.clicked.connect(self.loadConfigurationDialog)
        self.layout.addWidget(self.loadConfigButton)

        self.runButton = QPushButton("Run Experiment", self)
        self.runButton.clicked.connect(self.accept)
        self.runButton.setEnabled(False)  # Disabled until a valid config is loaded
        self.layout.addWidget(self.runButton)

        self.showDefaultMessage()

    def showDefaultMessage(self):
        # Show a default message or the experiment configuration UI based on the state
        if not self.experiment_config.config:  # No config loaded
            defaultMsgWidget = QLabel(
                "Please load a configuration file to begin.", self
            )
            defaultMsgWidget.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.parametersStack.addWidget(defaultMsgWidget)
            self.parametersStack.setCurrentWidget(defaultMsgWidget)
        else:  # Config loaded
            self.parametersStack.setCurrentWidget(self.experiment_config)

    def loadConfigurationDialog(self):
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration File", "", "YAML Files (*.yaml);;All Files (*)"
        )
        if fileName:
            self.loadConfiguration(fileName)

    def loadConfiguration(self, config_path):
        # Load and validate configuration, then switch to the configuration UI
        try:
            valid, message = self.experiment_config.loadConfiguration(config_path)
            self.runButton.setEnabled(valid)
            if valid:
                self.parametersStack.setCurrentWidget(self.experiment_config)
            else:
                QMessageBox.warning(self, "Configuration Validation Failed", message)
                self.showDefaultMessage()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Configuration Load Failed",
                f"Failed to load configuration: {str(e)}",
            )
            self.showDefaultMessage()

    def accept(self):
        """
        Commits the experiment configuration to schedule tasks based on the user's input.
        """
        steps = (
            self.experiment_config.getConfiguration()
            .get("experiment", {})
            .get("steps", [])
        )
        duration = timedelta(seconds=0)

        for step in steps:
            task_str: str = step.get("task")
            parameters = step.get("parameters", {})
            task_name_str = get_task_enum_value(task_str, self.task_enum)
            # Assuming 'TaskName' can resolve both names and values to an Enum member
            if not is_in_enum(task_str.strip(), self.task_enum):
                QMessageBox.critical(
                    self, "Error Scheduling Task", f"Unknown task: '{task_name_str}'"
                )
                return
            schedule_time = datetime.now() + duration
            try:
                # Schedule the task with timekeeper
                self.timekeeper.add_job(task_name_str, schedule_time, kwargs=parameters)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Scheduling Task",
                    f"Failed to schedule '{task_name_str}': {e}",
                )
                return  # Stop scheduling further tasks on error

            # Update total duration with the duration of the current step
            step_duration = timedelta(seconds=step.get("duration", 0))
            duration += step_duration

        self.callback()  # Trigger any post-scheduling actions
        super().accept()


class JobDetailsDialog(QDialog):
    def __init__(self, job_details, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Job Details")

        # Set a larger initial width for the dialog
        self.resize(400, 300)  # You can adjust the width and height as needed

        layout = QVBoxLayout(self)

        self.tableWidget = QTableWidget(self)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderLabels(["Field", "Value"])
        self.populate_table(job_details)

        # Set the table to expand to fill the dialog
        self.tableWidget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        layout.addWidget(self.tableWidget)

        closeButton = QPushButton("Close")
        closeButton.clicked.connect(self.accept)
        layout.addWidget(closeButton)

    def populate_table(self, job_details):
        self.tableWidget.setRowCount(len(job_details))
        for row, (key, value) in enumerate(job_details.items()):
            key_item = QTableWidgetItem(str(key))
            value_item = QTableWidgetItem(str(value))

            # Set the items to be non-editable
            key_item.setFlags(key_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            value_item.setFlags(value_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)

            self.tableWidget.setItem(row, 0, key_item)
            self.tableWidget.setItem(row, 1, value_item)

        # Resize columns to fit the content after populating the table
        self.tableWidget.resizeColumnsToContents()
        # Optionally, you can stretch the last section to fill the remaining space
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
