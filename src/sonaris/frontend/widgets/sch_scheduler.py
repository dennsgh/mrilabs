import json
from typing import Callable

from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sonaris import factory
from sonaris.frontend.widgets.sch_exp_popup import ExperimentConfigPopup
from sonaris.frontend.widgets.sch_task_popup import TaskConfigPopup, TaskDetailsDialog
from sonaris.scheduler.timekeeper import Timekeeper
from sonaris.utils import log as logutils
from sonaris.utils.log import get_logger

logger = get_logger()


class SchedulerWidget(QWidget):
    def __init__(self, timekeeper: Timekeeper = None, root_callback: Callable = None):
        super().__init__()
        self.timekeeper = timekeeper or factory.timekeeper
        self.job_popup = TaskConfigPopup(self.timekeeper, self.popup_callback)
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
                logger.info(f"Error removing job {job_id}: {e}")
        else:
            logger.info("No job selected")

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
                    dialog = TaskDetailsDialog(job_details, self)
                    dialog.exec()
            except FileNotFoundError:
                QMessageBox.warning(
                    self, "Error", "File not found. Could not retrieve job details."
                )
