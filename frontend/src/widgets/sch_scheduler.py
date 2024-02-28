import json
from datetime import datetime, timedelta
from typing import Callable, List

from features.task_validator import get_task_enum_value, is_in_enum
from features.tasks import TaskName, get_tasks
from header import DEVICE_LIST
from pages import factory
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from widgets.sch_experiments import ExperimentConfiguration
from widgets.sch_parameters import ParameterConfiguration

from scheduler.timekeeper import Timekeeper
from utils import logging as logutils


class SchedulerWidget(QWidget):
    def __init__(self, timekeeper: Timekeeper = None, root_callback: Callable = None):
        super().__init__()
        self.timekeeper = timekeeper or factory.timekeeper
        self.job_popup = JobConfigPopup(self.timekeeper, self.popup_callback)
        self.experiment_popup = ExperimentConfigPopup(
            self.timekeeper, self.popup_callback
        )
        self.timekeeper.set_callback(self.popup_callback)
        self.root_callback = root_callback
        self.initUI()

    def initUI(self):
        # Create a horizontal splitter
        splitter = QSplitter(QtCore.Qt.Orientation.Horizontal, self)

        # Left side widget and layout
        leftWidget = QWidget()
        leftLayout = QVBoxLayout(leftWidget)

        # Label and table for displaying current jobs
        self.jobsLabel = QLabel("Current Jobs:", leftWidget)
        leftLayout.addWidget(self.jobsLabel)

        # Create the table with 4 columns
        self.jobsTable = QTableWidget(0, 4, leftWidget)
        self.jobsTable.setHorizontalHeaderLabels(
            ["Job ID", "Task Name", "Scheduled Time", "Parameters"]
        )
        self.jobsTable.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.update_jobs_table()
        leftLayout.addWidget(self.jobsTable)

        # Button to configure a job
        self.configureJobButton = QPushButton("Schedule Task", leftWidget)
        self.configureJobButton.clicked.connect(self.open_job_config_popup)
        leftLayout.addWidget(self.configureJobButton)

        # Button to configure a job
        self.configureExperimentButton = QPushButton("Run Experiment", leftWidget)
        self.configureExperimentButton.clicked.connect(
            self.open_experiment_config_popup
        )
        leftLayout.addWidget(self.configureExperimentButton)

        self.removeJobButton = QPushButton("Remove Selected Job", leftWidget)
        self.removeJobButton.clicked.connect(self.remove_selected_job)
        leftLayout.addWidget(self.removeJobButton)

        # Right side widget and layout
        rightWidget = QWidget()
        rightLayout = QVBoxLayout(rightWidget)

        # Label and list for displaying finished jobs
        self.finishedJobsLabel = QLabel("Finished Jobs:", rightWidget)
        rightLayout.addWidget(self.finishedJobsLabel)

        self.finishedJobsTable = QTableWidget(rightWidget)
        self.finishedJobsTable.setColumnCount(
            3
        )  # Assuming you have 3 columns: Result, Task, Job ID
        self.finishedJobsTable.setHorizontalHeaderLabels(["Result", "Task", "Job ID"])
        self.finishedJobsTable.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.finishedJobsTable.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.finishedJobsTable.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.finishedJobsTable.cellDoubleClicked.connect(self.show_archive_entry)

        self.update_finished_jobs_list()
        rightLayout.addWidget(self.finishedJobsTable)

        self.clearFinishedJobsButton = QPushButton("Clear Archive", rightWidget)
        self.clearFinishedJobsButton.clicked.connect(self.clear_finished_jobs)
        rightLayout.addWidget(self.clearFinishedJobsButton)
        # Add the left and right widgets to the splitter
        splitter.addWidget(leftWidget)
        splitter.addWidget(rightWidget)

        # Optionally set initial sizes of the splitter sections
        splitter.setSizes([300, 200])  # Adjust these values as needed

        # Set the main layout to include the splitter
        mainLayout = QVBoxLayout(self)
        mainLayout.addWidget(splitter)

    def update_jobs_table(self):
        self.jobsTable.setRowCount(0)
        jobs = self.timekeeper.get_jobs()
        for job_id, job_info in jobs.items():
            row_position = self.jobsTable.rowCount()
            self.jobsTable.insertRow(row_position)

            # Create QTableWidgetItem for each entry and set it to non-editable
            job_id_item = QTableWidgetItem(job_id)
            job_id_item.setFlags(
                job_id_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
            )
            self.jobsTable.setItem(row_position, 0, job_id_item)

            task_name_item = QTableWidgetItem(job_info["task"])
            task_name_item.setFlags(
                task_name_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
            )
            self.jobsTable.setItem(row_position, 1, task_name_item)

            schedule_time_item = QTableWidgetItem(job_info["schedule_time"])
            schedule_time_item.setFlags(
                schedule_time_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
            )
            self.jobsTable.setItem(row_position, 2, schedule_time_item)

            parameters_item = QTableWidgetItem(str(job_info["kwargs"]))
            parameters_item.setFlags(
                parameters_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
            )
            self.jobsTable.setItem(row_position, 3, parameters_item)

    def remove_selected_job(self):
        selected_items = self.jobsTable.selectedItems()
        if selected_items:
            selected_row = selected_items[0].row()
            job_id = self.jobsTable.item(selected_row, 0).text()
            try:
                self.timekeeper.cancel_job(job_id)
                self.update_jobs_table()
            except Exception as e:
                print(f"Error removing job {job_id}: {e}")
        else:
            print("No job selected")

    def update_finished_jobs_list(self):
        self.finishedJobsTable.setRowCount(0)  # Clear the existing rows in the table
        finished_jobs = logutils.load_json_with_backup(self.timekeeper.archive)

        for job_id, job_info in finished_jobs.items():
            row_position = self.finishedJobsTable.rowCount()
            self.finishedJobsTable.insertRow(row_position)

            result_item = QTableWidgetItem(
                "OK" if job_info.get("result", False) else "ERR"
            )
            task_item = QTableWidgetItem(job_info.get("task", ""))
            job_id_item = QTableWidgetItem(job_id)

            result_item.setFlags(
                result_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
            )
            task_item.setFlags(task_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            job_id_item.setFlags(
                job_id_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
            )

            self.finishedJobsTable.setItem(row_position, 0, result_item)
            self.finishedJobsTable.setItem(row_position, 1, task_item)
            self.finishedJobsTable.setItem(row_position, 2, job_id_item)

    def clear_finished_jobs(self):
        # Confirmation message box
        reply = QMessageBox.question(
            self,
            "Clear Archive",
            "Are you sure you want to clear the archive?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        # Check if the user confirmed the action
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.timekeeper.clear_archive()
                self.update_finished_jobs_list()
                QMessageBox.information(
                    self, "Success", "The archive has been cleared."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", "Could not clear the archive.")

    def open_job_config_popup(self):
        self.job_popup.exec()

    def open_experiment_config_popup(self):
        self.experiment_popup.exec()

    def popup_callback(self):
        self.update_jobs_table()
        self.update_finished_jobs_list()
        if self.root_callback is not None:
            # Relay tick to main app.
            self.root_callback()

    def show_archive_entry(self, row, column):
        job_id_item = self.finishedJobsTable.item(
            row, 2
        )  # Assuming Job ID is in the 3rd column
        if job_id_item:
            job_id = job_id_item.text()
            try:
                with self.timekeeper.archive.open("r") as file:
                    finished_jobs = json.load(file)
                job_details = finished_jobs.get(job_id, {})
                if job_details:
                    dialog = JobDetailsDialog(job_details, self)
                    dialog.exec()
            except FileNotFoundError:
                QMessageBox.warning(
                    self, "Error", "File not found. Could not retrieve job details."
                )


class JobConfigPopup(QDialog):
    NO_TASK_STRING = "No tasks available"

    def __init__(self, timekeeper: Timekeeper, _callback: Callable):
        super().__init__()
        self.resize(800, 320)
        self.task_dict = get_tasks(flatten=False)
        self.task_enum = TaskName
        self.parameterConfig = ParameterConfiguration(
            task_dictionary=self.task_dict, parent=self, task_enum=self.task_enum
        )

        self.timekeeper = timekeeper
        self.tasks = get_tasks()
        self._callback = _callback
        self.deviceSelect = QComboBox(self)
        self.taskSelect = QComboBox(self)

        # Add items to device select combo box and set initial selection
        self.deviceSelect.addItems(DEVICE_LIST)
        if self.deviceSelect.count() > 0:
            self.deviceSelect.setCurrentIndex(0)  # Set initial value to first option
            self.updateTaskList()  # Update task list based on selected device

        # Connect signals
        self.deviceSelect.currentIndexChanged.connect(self.updateTaskList)
        self.taskSelect.currentIndexChanged.connect(self.updateUI)

        self.initUI()

    def initUI(self):
        # Overall grid layout
        gridLayout = QGridLayout(self)

        # Configuration group at the top
        configurationGroup = QGroupBox("Configuration")
        configurationLayout = QVBoxLayout(configurationGroup)
        configurationLayout.addWidget(QLabel("Select Device:"))
        configurationLayout.addWidget(self.deviceSelect)
        configurationLayout.addWidget(QLabel("Select Task:"))
        configurationLayout.addWidget(self.taskSelect)
        gridLayout.addWidget(configurationGroup, 0, 0, 1, 2)  # Span 1 row, 2 columns

        # Time configuration on the second row, left side
        timeConfigGroup = QGroupBox()
        timeConfigLayout = QHBoxLayout(timeConfigGroup)
        self.timeConfigComboBox = QComboBox(self)
        self.timeConfigComboBox.addItems(["Timedelta", "Timestamp"])
        timeConfigLayout.addWidget(self.timeConfigComboBox)
        self.setupTimeConfiguration(timeConfigLayout)  # Add time configuration widgets
        gridLayout.addWidget(
            timeConfigGroup, 1, 0
        )  # This will be on the second row, first column

        # Parameter configuration on the second row, right side, taking up two columns
        parameterConfigGroup = QGroupBox("Parameter Configuration")
        parameterConfigLayout = QVBoxLayout(parameterConfigGroup)
        parameterConfigLayout.addWidget(self.parameterConfig)
        gridLayout.addWidget(
            parameterConfigGroup, 1, 1
        )  # This will be on the second row, second column

        # Adjust the column stretch factors according to the desired ratio
        gridLayout.setColumnStretch(
            0, 1
        )  # This sets the stretch factor for the first column
        gridLayout.setColumnStretch(
            1, 2
        )  # This sets the stretch factor for the second column
        gridLayout.setRowStretch(0, 1)  # Smaller first row (20%)
        gridLayout.setRowStretch(1, 4)  # Larger second row (80%)
        # Third row for OK and Cancel buttons
        buttonsLayout = QHBoxLayout()
        self.okButton = QPushButton("OK", self)
        self.okButton.clicked.connect(self.accept)
        buttonsLayout.addWidget(self.okButton)
        self.cancelButton = QPushButton("Cancel", self)
        self.cancelButton.clicked.connect(self.reject)
        buttonsLayout.addWidget(self.cancelButton)

        # Add the buttonsLayout to the grid
        gridLayout.addLayout(buttonsLayout, 2, 0, 1, 2)  # Span 1 row and 2 columns

        # Set the layout for the QDialog
        self.setLayout(gridLayout)

    def updateTimeConfigurationVisibility(self, selection):
        isTimestamp = selection == "Timestamp"
        self.timestampWidget.setVisible(isTimestamp)
        self.durationWidget.setVisible(not isTimestamp)

    def updateTaskList(self):
        selected_device = self.deviceSelect.currentText()
        tasks = self.tasks.get(selected_device, {}).keys()
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
        # Create a grid layout for timestamp inputs
        gridLayout = QGridLayout()
        self.timestampInputs = {}  # Dictionary to hold references to QLineEdit widgets

        # Define the fields and their positions in the grid
        fields = [
            ("Year", "year", 0, 0),
            ("Month", "month", 1, 0),
            ("Day", "day", 2, 0),
            ("Hour", "hour", 0, 1),
            ("Minute", "minute", 1, 1),
            ("Second", "second", 2, 1),
            ("Millisecond", "millisecond", 3, 1),
        ]

        # Add the labels and line edits to the grid layout
        for label_text, field, row, col in fields:
            label = QLabel(f"{label_text}:")
            lineEdit = QLineEdit(self)
            lineEdit.setText(str(getattr(default_value, field, 0)))
            gridLayout.addWidget(label, row, col * 2)
            gridLayout.addWidget(lineEdit, row, col * 2 + 1)
            self.timestampInputs[field] = lineEdit  # Store QLineEdit reference

        return gridLayout

    def createDurationInputs(self):
        # Create a grid layout for duration inputs
        gridLayout = QGridLayout()
        self.durationInputs = {}  # Dictionary to hold references to QLineEdit widgets

        # Define the fields and their positions in the grid
        fields = [
            ("Days", "days", 0, 0),
            ("Hours", "hours", 0, 1),
            ("Minutes", "minutes", 1, 1),
            ("Seconds", "seconds", 2, 1),
            ("Milliseconds", "milliseconds", 3, 1),
        ]

        # Add the labels and line edits to the grid layout
        for label_text, field, row, col in fields:
            label = QLabel(f"{label_text}:")
            lineEdit = QLineEdit(self)
            lineEdit.setText("00")  # Default value set to "00"
            gridLayout.addWidget(label, row, col * 2)
            gridLayout.addWidget(lineEdit, row, col * 2 + 1)
            self.durationInputs[field] = lineEdit  # Store QLineEdit reference

        # Add an empty label to balance the layout
        gridLayout.addWidget(QLabel(""), 2, 0)

        return gridLayout

    def toggleTimeInputs(self):
        # Toggle visibility of time input fields based on selected option
        isTimestamp = bool(self.timeConfigComboBox.currentText().lower() == "timestamp")
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
            self._callback()
            super().accept()
        except Exception as e:
            print({f"Error during commissioning job on : {e}"})

    def getDateTimeFromInputs(self):
        # Create a datetime or timedelta object from input fields
        if self.timeConfigComboBox.currentText().lower() == "timestamp":
            # Assuming self.timestampInputs is a dictionary of QLineEdit widgets keyed by field names
            return datetime(
                year=int(self.timestampInputs["year"].text()),
                month=int(self.timestampInputs["month"].text()),
                day=int(self.timestampInputs["day"].text()),
                hour=int(self.timestampInputs["hour"].text()),
                minute=int(self.timestampInputs["minute"].text()),
                second=int(self.timestampInputs["second"].text()),
                microsecond=int(self.timestampInputs["millisecond"].text()) * 1000,
            )
        else:
            # Assuming self.durationInputs is a dictionary of QLineEdit widgets keyed by field names
            duration = timedelta(
                days=int(self.durationInputs["days"].text()),
                hours=int(self.durationInputs["hours"].text()),
                minutes=int(self.durationInputs["minutes"].text()),
                seconds=int(self.durationInputs["seconds"].text()),
                milliseconds=int(self.durationInputs["milliseconds"].text()),
            )
            return datetime.now() + duration


class ExperimentConfigPopup(QDialog):
    def __init__(self, timekeeper: Timekeeper, _callback: Callable, parent=None):
        super().__init__(parent)
        self.timekeeper = timekeeper
        self._callback = _callback
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
        self.resize(250, 150)  # Adjust size as needed
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

        self._callback()  # Trigger any post-scheduling actions
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


# if __name__ == "__main__":
#     import sys

#     # === FOR DEBUGGING=== #
#     from scheduler.worker import Worker

#     factory.worker = Worker(
#         function_map_file=factory.FUNCTION_MAP_FILE,
#         logfile=factory.WORKER_LOGS,
#     )
#     factory.timekeeper = Timekeeper(
#         persistence_file=factory.TIMEKEEPER_JOBS_FILE,
#         worker_instance=factory.worker,
#         logfile=factory.TIMEKEEPER_LOGS,
#     )
#     for task_name, func_pointer in get_tasks():
#         factory.worker.register_task(func_pointer, task_name)
#     # === FOR DEBUGGING=== #

#     app_qt = QApplication(sys.argv)
#     ex = SchedulerWidget(timekeeper=factory.timekeeper)
#     ex.show()
#     sys.exit(app_qt.exec())
