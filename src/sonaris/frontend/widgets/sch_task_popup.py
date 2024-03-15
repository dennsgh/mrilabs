from datetime import datetime, timedelta
from typing import Callable

import yaml
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sonaris.defaults import DELAY_KEYWORD, TASKS_MISSING, TIMESTAMP_KEYWORD
from sonaris.frontend.widgets.sch_task_parameters import TaskParameterConfiguration
from sonaris.scheduler.timekeeper import Timekeeper
from sonaris.tasks.model import Experiment, Task
from sonaris.tasks.task_validator import Validator
from sonaris.tasks.tasks import TaskName, get_tasks
from sonaris.utils.log import get_logger

logger = get_logger()


class TaskConfigPopup(QDialog):

    def __init__(self, timekeeper: Timekeeper, callback: Callable):
        super().__init__()
        self.resize(864, 400)
        self.task_dict = get_tasks(flatten=False)
        self.task_enum = TaskName
        self.timekeeper = timekeeper
        self.callback = callback

        self.initUI()
        self.connectSignals()
        self.updateTaskList()

    def initUI(self):
        self.setWindowTitle("Scheduler")
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
        self.timeConfigComboBox.addItems([DELAY_KEYWORD, TIMESTAMP_KEYWORD])
        timeConfigLayout.addWidget(self.timeConfigComboBox)

        self.setupTimeConfiguration(timeConfigLayout)
        self.gridLayout.addWidget(timeConfigGroup, 1, 0)

    def setupParameterConfigurationGroup(self):
        self.parameterConfig = TaskParameterConfiguration(
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

        if (
            self.timeConfigComboBox.currentText() == "TIMESTAMP"
        ):  # Assuming TIMESTAMP_KEYWORD is "TIMESTAMP"
            schedule_time = self.getDateTimeFromInputs()
            # Calculate the delay as the difference between the schedule time and now
            delay = (schedule_time - now).total_seconds()
        else:
            # Directly use the delay from the inputs if "delay" is selected
            delay = (self.getDateTimeFromInputs() - now).total_seconds()

        # Ensure delay is always positive before displaying
        delay = max(0, delay)  # Reset to 0 if negative

        # Use the Task and Experiment models to create the configuration
        task_name = Validator.get_task_enum_name(
            self.taskSelect.currentText(),
            self.task_enum,  # Assuming you have task_enum available
        )

        task = Task(
            task=task_name,
            delay=delay,
            description=f"{self.taskSelect.currentText()} at time {delay}s",
            parameters=parameters,
        )

        # Wrap the task in an Experiment model
        experiment = Experiment(name="unnamed", steps=[task])

        # Convert the Experiment model instance to YAML string for display
        yamlStr = yaml.dump(
            experiment.dict(), sort_keys=False, default_flow_style=False
        )
        self.yamlDisplayWidget.setText(yamlStr)

    def updateTimeConfigurationVisibility(self, selection):
        isTimestamp = selection == TIMESTAMP_KEYWORD
        self.timestampWidget.setVisible(isTimestamp)
        self.delayWidget.setVisible(not isTimestamp)

    def updateTaskList(self):
        selected_device = self.deviceSelect.currentText()
        tasks = self.task_dict.get(selected_device, {}).keys()
        self.taskSelect.clear()
        if tasks:
            self.taskSelect.addItems(tasks)
            self.taskSelect.setCurrentIndex(0)
        else:
            self.taskSelect.addItem(TASKS_MISSING)
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
        self.delayWidget = QWidget(self)
        self.timestampWidget = QWidget(self)

        # Set grid layouts to these widgets
        timestampGridLayout = self.createDateTimeInputs(datetime.now())
        waitGridLayout = self.createwaitInputs()
        self.timestampWidget.setLayout(timestampGridLayout)
        self.delayWidget.setLayout(waitGridLayout)

        # Add these widgets to the main layout
        layout.addWidget(self.timestampWidget)
        layout.addWidget(self.delayWidget)

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

    def createwaitInputs(self):
        gridLayout = QGridLayout()
        self.waitInputs = {}

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
            self.waitInputs[field] = inputWidget

        return gridLayout

    def toggleTimeInputs(self):
        # Toggle visibility of time input fields based on selected option
        isTimestamp = bool(self.timeConfigComboBox.currentText() == TIMESTAMP_KEYWORD)
        for input in self.timestampInputs:
            input.setVisible(isTimestamp)
        for input in self.waitInputs:
            input.setVisible(not isTimestamp)

    def accept(self):
        # Schedule the task with either timestamp or delay
        selected_task = self.taskSelect.currentText()
        schedule_time = self.getDateTimeFromInputs()
        try:
            # Get parameters from TaskParameterConfiguration
            params = self.parameterConfig.getConfiguration()

            self.timekeeper.add_job(
                task_name=selected_task, schedule_time=schedule_time, kwargs=params
            )
            # Callback to update the UI, etc.
            self.callback()
            super().accept()
        except Exception as e:
            logger.info({f"Error during commissioning task on : {e}"})

    def getDateTimeFromInputs(self):
        if self.timeConfigComboBox.currentText() == TIMESTAMP_KEYWORD:
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
            delay = timedelta(
                days=self.waitInputs["days"].value(),
                hours=self.waitInputs["hours"].value(),
                minutes=self.waitInputs["minutes"].value(),
                seconds=self.waitInputs["seconds"].value(),
                milliseconds=int(
                    self.waitInputs["milliseconds"].value()
                ),  # Ensure integer for milliseconds
            )
            return datetime.now() + delay


class TaskDetailsDialog(QDialog):
    def __init__(self, task_details, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Task Details")

        # Set a larger initial width for the dialog
        self.resize(400, 300)  # You can adjust the width and height as needed

        layout = QVBoxLayout(self)

        self.tableWidget = QTableWidget(self)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderLabels(["Field", "Value"])
        self.populate_table(task_details)

        # Set the table to expand to fill the dialog
        self.tableWidget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        layout.addWidget(self.tableWidget)

        closeButton = QPushButton("Close")
        closeButton.clicked.connect(self.accept)
        layout.addWidget(closeButton)

    def populate_table(self, task_details):
        self.tableWidget.setRowCount(len(task_details))
        for row, (key, value) in enumerate(task_details.items()):
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
