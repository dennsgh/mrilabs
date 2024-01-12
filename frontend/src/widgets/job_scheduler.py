import json
from datetime import datetime, timedelta
from typing import Callable

from header import DEVICE_LIST, TASK_USER_INTERFACE_DICTIONARY, get_tasks
from pages import factory
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from widgets.parameters import ParameterConfiguration

from scheduler.timekeeper import Timekeeper


class SchedulerWidget(QWidget):
    def __init__(self, timekeeper: Timekeeper = None, root_callback: Callable = None):
        super().__init__()
        self.timekeeper = timekeeper or factory.timekeeper
        self.popup = JobConfigPopup(self.timekeeper, self.popup_callback)
        self.timekeeper.set_callback(self.popup_callback)
        self.root_callback = root_callback
        self.initUI()

    def initUI(self):
        # Create a horizontal splitter
        splitter = QSplitter(QtCore.Qt.Orientation.Horizontal, self)

        # Left side widget and layout
        leftWidget = QWidget()
        leftLayout = QVBoxLayout(leftWidget)

        # DateTime picker for scheduling tasks
        self.dateTimeEdit = QDateTimeEdit(leftWidget)
        self.dateTimeEdit.setDateTime(datetime.now())
        leftLayout.addWidget(self.dateTimeEdit)

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

        self.removeJobButton = QPushButton("Remove Selected Job", leftWidget)
        self.removeJobButton.clicked.connect(self.remove_selected_job)
        leftLayout.addWidget(self.removeJobButton)

        # Right side widget and layout
        rightWidget = QWidget()
        rightLayout = QVBoxLayout(rightWidget)

        # Label and list for displaying finished jobs
        self.finishedJobsLabel = QLabel("Finished Jobs:", rightWidget)
        rightLayout.addWidget(self.finishedJobsLabel)

        self.finishedJobsList = QListWidget(rightWidget)
        self.finishedJobsList.itemDoubleClicked.connect(self.show_archive_entry)
        self.update_finished_jobs_list()
        rightLayout.addWidget(self.finishedJobsList)

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
        self.finishedJobsList.clear()
        try:
            with self.timekeeper.archive.open("r") as file:
                finished_jobs = json.load(file)
            for job_id, job_info in finished_jobs.items():
                self.finishedJobsList.addItem(f"{job_info['task']}   \t - [{job_id}]")
        except FileNotFoundError:
            pass

    def clear_finished_jobs(self):
        try:
            self.timekeeper.clear_archive()
            self.update_finished_jobs_list()
        except Exception as e:
            print(f"Error clearing finished jobs: {e}")

    def open_job_config_popup(self):
        self.popup.exec()

    def popup_callback(self):
        self.update_jobs_table()
        self.update_finished_jobs_list()
        if self.root_callback is not None:
            # Relay tick to main app.
            self.root_callback()

    def show_archive_entry(self, item):
        # Get the text of the double-clicked item
        item_text = item.text()

        # Extract the job ID from the text (assuming it's enclosed in square brackets [])
        job_id_start = item_text.find("[")
        job_id_end = item_text.find("]")

        if job_id_start != -1 and job_id_end != -1:
            job_id = item_text[job_id_start + 1 : job_id_end]

            # Retrieve the job details from the archive using the job_id
            try:
                with self.timekeeper.archive.open("r") as file:
                    finished_jobs = json.load(file)
                job_details = finished_jobs.get(job_id)
                if job_details:
                    # Display the job details using a QMessageBox or any other method
                    QMessageBox.information(
                        self, "Job Details", f"Job ID: {job_id}\nDetails: {job_details}"
                    )
            except FileNotFoundError:
                pass


class JobConfigPopup(QDialog):
    def __init__(self, timekeeper: Timekeeper, _callback: Callable):
        super().__init__()
        self.resize(800, 320)
        self.parameterConfig = ParameterConfiguration(self)
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
        self.taskSelect.currentIndexChanged.connect(self.updateParameterUI)

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
        # Update the task list based on the selected device
        selected_device = self.deviceSelect.currentText()
        tasks = self.tasks.get(selected_device, {}).keys()
        self.taskSelect.clear()
        self.taskSelect.addItems(tasks)
        if self.taskSelect.count() > 0:
            self.taskSelect.setCurrentIndex(0)  # Set initial value to first option
        # Update parameter UI based on initial selections
        self.updateParameterUI()

    def updateParameterUI(self):
        selected_device = self.deviceSelect.currentText()
        selected_task = self.taskSelect.currentText()
        self.parameterConfig.updateUI(selected_device, selected_task)

    def updateUI(self):
        selected_device = self.deviceSelect.currentText()
        selected_task = self.taskSelect.currentText()
        self.parameterConfig.updateUI(selected_device, selected_task)

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
        selected_device = self.deviceSelect.currentText()
        selected_task = self.taskSelect.currentText()
        schedule_time = self.getDateTimeFromInputs()
        try:
            task_spec = TASK_USER_INTERFACE_DICTIONARY[selected_device][selected_task]

            # Get parameters from ParameterConfiguration
            params = self.parameterConfig.get_parameters(task_spec)

            self.timekeeper.add_job(
                task_name=selected_task, schedule_time=schedule_time, kwargs=params
            )
            # Callback to update the UI, etc.
            self._callback()
            super().accept()
        except Exception as e:
            print(
                {
                    f"Error during commissioning job on {selected_device} - {selected_task} : {e}"
                }
            )

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

    def getParameters(self):
        # to implement
        return {}


# Rest of the application code remains the same


if __name__ == "__main__":
    import sys

    # === FOR DEBUGGING=== #
    from scheduler.worker import Worker

    factory.worker = Worker(
        function_map_file=factory.FUNCTION_MAP_FILE,
        logfile=factory.WORKER_LOGS,
    )
    factory.timekeeper = Timekeeper(
        persistence_file=factory.TIMEKEEPER_JOBS_FILE,
        worker_instance=factory.worker,
        logfile=factory.TIMEKEEPER_LOGS,
    )
    for task_name, func_pointer in get_tasks():
        factory.worker.register_task(func_pointer, task_name)
    # === FOR DEBUGGING=== #

    app_qt = QApplication(sys.argv)
    ex = SchedulerWidget(timekeeper=factory.timekeeper)
    ex.show()
    sys.exit(app_qt.exec())