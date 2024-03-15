from datetime import datetime, timedelta
from typing import Callable

from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
)

from sonaris.defaults import DELAY_KEYWORD, EXPERIMENT_KEYWORD
from sonaris.frontend.widgets.sch_experiments import ExperimentConfiguration
from sonaris.scheduler.timekeeper import Timekeeper
from sonaris.tasks.task_validator import Validator
from sonaris.tasks.tasks import TaskName, get_tasks
from sonaris.utils.log import get_logger

logger = get_logger()


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
        self.setWindowTitle("Experiment Scheduler")
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
        if not self.experiment_config.get_experiment():  # No config loaded
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

    def loadConfiguration(self, config_path: str):
        # Load and validate configuration, then switch to the configuration UI
        try:
            valid, message = self.experiment_config.loadConfiguration(config_path)
            self.runButton.setEnabled(valid)
            if valid:
                self.parametersStack.setCurrentWidget(self.experiment_config)
            else:
                QMessageBox.warning(self, "Configuration Validation Failed", message)
                logger.warning(message)
                self.showDefaultMessage()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Configuration Load Failed",
                f"Failed to load configuration: {str(e)}",
            )
            logger.error(f"Error: {e} {message}")
            self.showDefaultMessage()

    def accept(self):
        """
        Commits the experiment configuration to schedule tasks based on the user's input.
        """
        steps = self.experiment_config.getConfiguration().steps

        for step in steps:
            step_delay = timedelta(seconds=step.delay if step.delay else 0.0)
            task_str: str = step.task
            parameters = step.parameters
            task_name_str = Validator.get_task_enum_value(task_str, self.task_enum)
            # Assuming 'TaskName' can resolve both names and values to an Enum member
            if not Validator.is_in_enum(task_str.strip(), self.task_enum):
                QMessageBox.critical(
                    self, "Error Scheduling Task", f"Unknown task: '{task_name_str}'"
                )
                logger.error(f"Unknown task: '{task_name_str}'")
                return
            schedule_time = datetime.now() + step_delay
            try:
                # Schedule the task with timekeeper
                self.timekeeper.add_job(task_name_str, schedule_time, kwargs=parameters)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Scheduling Task",
                    f"Failed to schedule '{task_name_str}': {e}",
                )
                logger.error(f"Unknown task: '{task_name_str}: {e}'")
                return  # Stop scheduling further tasks on error

        self.callback()  # Trigger any post-scheduling actions
        super().accept()
