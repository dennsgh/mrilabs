import inspect
import traceback
from enum import Enum
from typing import Any, Callable, Dict, List

import yaml
from pydantic import ValidationError
from PyQt6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sonaris.defaults import DELAY_KEYWORD, ErrorLevel
from sonaris.frontend.widgets.ui_factory import UIComponentFactory
from sonaris.tasks.model import Experiment, ExperimentWrapper, Task
from sonaris.tasks.task_validator import Validator
from sonaris.utils.log import get_logger

logger = get_logger()


class ExperimentConfiguration(QWidget):
    """
    A widget that displays and interacts with experiment configurations.

    This widget allows users to load, view, and edit experiment configurations
    defined in YAML format. It also handles validation and saving of the configuration.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        task_functions: dict[str, object] | None = None,
        task_enum: Enum | None = None,
        logger=None,
    ) -> None:
        """
        Initializes the widget.

        Args:
            parent: The parent widget of this widget. Defaults to None.
            task_functions: A dictionary mapping task names to their corresponding functions. Defaults to None.
            task_enum: An enumeration representing the valid task types. Defaults to None.
        """
        super().__init__(parent)
        self.__safe__ = True
        self.logger = logger or get_logger()
        self.task_functions: dict[str, Callable] = task_functions
        self.task_enum: Enum = task_enum
        self.experiment: Experiment | None = None
        self.validator = Validator(
            task_functions=self.task_functions, task_enum=self.task_enum
        )
        self.initUI()

    def initUI(self):
        # Main horizontal layout
        self.mainHLayout = QHBoxLayout(self)
        # Left vertical layout for tabs and configuration details
        self.leftVLayout = QVBoxLayout()
        self.tabWidget = QTabWidget(self)
        self.descriptionWidget = QTextEdit(self)
        self.descriptionWidget.setReadOnly(True)
        self.descriptionWidget.setText(
            "Load an experiment configuration to see its details here."
        )

        # Add widgets to the left layout
        self.leftVLayout.addWidget(self.tabWidget)
        self.leftVLayout.addWidget(self.descriptionWidget)

        # Right vertical layout for YAML display
        self.rightVLayout = QVBoxLayout()
        self.yamlDisplayWidget = QTextEdit(self)
        self.yamlDisplayWidget.setReadOnly(True)

        # Add YAML display widget to the right layout
        self.rightVLayout.addWidget(self.yamlDisplayWidget)

        # Add both left and right layouts to the main layout
        self.mainHLayout.addLayout(
            self.leftVLayout, 3
        )  # 3: proportion of space taken by left layout
        self.mainHLayout.addLayout(
            self.rightVLayout, 2
        )  # 2: proportion of space taken by right layout

        # Connect tab change signal to update YAML display
        self.tabWidget.currentChanged.connect(self.onTabChanged)

        # Adjust size policies for responsive layout
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tabWidget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.descriptionWidget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.yamlDisplayWidget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    def onTabChanged(self):
        """Updates the YAML display when the user changes tabs."""
        self.updateYamlDisplay()

    def updateYamlDisplay(self):
        if self.__safe__:
            self.__updateYamlDisplay()

    def __updateYamlDisplay(self):
        currentTabIndex = self.tabWidget.currentIndex()
        if currentTabIndex != -1:
            step_config = self.getUserData().steps[currentTabIndex]
            yamlStr = yaml.dump(step_config.model_dump(), sort_keys=False)
            self.yamlDisplayWidget.setText(yamlStr)

    def loadConfiguration(self, config_path: str):

        with open(config_path, "r") as file:
            raw_dict = yaml.safe_load(file)

        if not raw_dict:
            QMessageBox.warning(self, "Error", "No configuration loaded.")
            logger.warning(f"No configuration loaded at {config_path}.")
            return False, "No configuration loaded.", {}

        raw_exp = ExperimentWrapper(**raw_dict).experiment
        overall_valid, message_dict, highest_error_level = self.validate(raw_exp)
        descriptionText = self.errorHandling(
            overall_valid, message_dict, highest_error_level
        )  # determine the description text.

        self.descriptionWidget.setText(descriptionText)
        if overall_valid:
            self.__safe__ = False
            self.experiment = raw_exp
            self.displayExperimentDetails()
            self.update()
            self.__safe__ = True
            logger.info(f"{config_path} loaded successfully.")
            return True, "Configuration loaded successfully."
        else:
            logger.warning(f"{config_path} was unable to be parsed.")
            logger.warning(
                f"{highest_error_level.value} error level: {highest_error_level.name}"
            )
            logger.warning(
                "\n".join([f"{key} : {value}" for key, value in message_dict.items()])
            )
            return False, "Failed to load or parse the configuration."

    def validate(self, experiment: Experiment) -> tuple[bool, dict, ErrorLevel]:
        try:
            validation_results = self.validator.validate_configuration(experiment)
            message_dict = {"errors": [], "warnings": [], "infos": []}
            overall_valid = True
            highest_error_level = ErrorLevel.INFO

            for task_name, is_valid, message, error_level in validation_results:
                if not is_valid:
                    overall_valid = False
                    message_dict["errors"].append(f"{task_name}: {message}")
                    if error_level.value > highest_error_level.value:
                        highest_error_level = error_level
                else:
                    message_dict["infos"].append(f"{task_name}: {message}")
            return overall_valid, message_dict, highest_error_level
        except ValidationError as e:
            self.logger.error(f"Validation error: {str(e)} {traceback.format_exc()}")
            return False, {"errors": [str(e)]}, ErrorLevel.INVALID_YAML

    def errorHandling(
        self, overall_valid: bool, message_dict: dict, highest_error_level: ErrorLevel
    ) -> str:
        descriptionText = "---\n"

        if message_dict["errors"]:
            descriptionText += "\nErrors:\n" + "\n".join(message_dict["errors"])
        if message_dict["warnings"]:
            descriptionText += "\nWarnings:\n" + "\n".join(message_dict["warnings"])

        infos_with_content = [
            info
            for info in message_dict["infos"]
            if "Validation issues:" not in info or len(info.split(":")) > 2
        ]
        if infos_with_content:
            descriptionText += "\nInformation:\n" + "\n".join(infos_with_content)

        if overall_valid or highest_error_level == ErrorLevel.INFO:
            descriptionText = (
                self.generate_experiment_summary(self.experiment)
                + "\n"
                + descriptionText
            )

        return descriptionText

    def get_experiment(self):
        return self.experiment

    def displayExperimentDetails(self) -> None:
        """
        Displays the details of the loaded experiment configuration in a tabbed interface.

        Creates tabs for each step in the experiment and populates them with
        widgets for interacting with the step parameters.

        Raises a warning message if no configuration is loaded.
        """
        if not self.experiment:
            QMessageBox.warning(self, "Error", "No configuration loaded.")
            return

        self.tabWidget.clear()
        steps = self.experiment.steps
        if steps:
            for index, step in enumerate(steps, start=1):
                valid, err = self.createTaskTab(step)
                if not valid:
                    QMessageBox.warning(
                        self, "Warning", f"At step {index} [{step}]:{err}"
                    )
        self.layout().update()
        self.__updateYamlDisplay()

    def createTaskTab(self, task: Task) -> bool:
        """
        Generates a tab with a form layout for each step, allowing users to
        interact with the step parameters.

        Args:
            task: A dictionary representing a single experiment step.
        """

        tab = QWidget()
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        layout = QVBoxLayout(tab)
        layout.addWidget(scrollArea)
        formWidget = QWidget()
        formLayout = QFormLayout()

        delay = task.delay
        delayWidget = UIComponentFactory.create_widget(
            DELAY_KEYWORD, delay or 0.0, float, None, lambda: self.updateYamlDisplay()
        )
        delayWidget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        formLayout.addRow(QLabel(f"{DELAY_KEYWORD} (s):"), delayWidget)
        formWidget.setLayout(formLayout)
        try:
            task_function = self.get_function(task)
            if not task_function:
                return (
                    False,
                    "Function not Found, task name is not associated with a function.",
                )

            # Inspect the function signature to get parameter information
            sig = inspect.signature(task_function)
            param_types = {
                name: param.annotation for name, param in sig.parameters.items()
            }
            parameter_annotations = getattr(task_function, "parameter_annotations", {})
            parameter_constraints = getattr(task_function, "parameter_constraints", {})
            # Initialize a dictionary to store the task parameters from the configuration
            task_parameters = task.parameters

            # trunk-ignore(ruff/B007)
            for parameter_name, param in sig.parameters.items():
                value = task_parameters.get(parameter_name, None)
                expected_type = param_types.get(
                    parameter_name, str
                )  # Defaults to string.
                # The units are embedded on the annotations for each parameter where applicable (if exist)
                param_unit = (
                    f"({parameter_annotations.get(parameter_name)})"
                    if parameter_annotations.get(parameter_name)
                    else ""
                )
                # Now, extract specific constraints for the current parameter
                specific_constraints = parameter_constraints.get(parameter_name, None)

                widget = UIComponentFactory.create_widget(
                    parameter_name,
                    value,
                    expected_type,
                    specific_constraints,
                    lambda: self.updateYamlDisplay(),
                )
                widget.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
                )
                # Create labels for parameter name and type hinting (optional)
                paramNameLabel = QLabel(
                    f"{parameter_name} :{expected_type.__name__} {param_unit}"
                )
                # Add labels and widget to the form layout
                formLayout.addRow(paramNameLabel, widget)

            scrollArea.setWidget(formWidget)
            self.tabWidget.addTab(
                tab, self.validator.get_task_enum_value(task.task, self.task_enum)
            )
            layout.addStretch(1)
            scrollArea.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            tab.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            return True, ""
        except Exception as e:
            logger.error(
                f"Failed to create task tab: {str(e)} {traceback.format_exc()}"
            )
            return False, f"{e}"

    def getUserData(self) -> Experiment:
        if not self.experiment:
            QMessageBox.warning(self, "Error", "No valid configuration loaded.")
            return {}

        # Extract the name from the configuration to use in the new experiment model
        experiment_name = self.experiment.name

        # Initialize an empty list to collect Task models
        tasks: List[Task] = []
        for index in range(self.tabWidget.count()):
            if index >= len(self.experiment.steps):
                continue

            step_widget = self.tabWidget.widget(index)
            form_widget = step_widget.findChild(QScrollArea).widget()
            form_layout = form_widget.layout()

            original_step = self.experiment.steps[index]
            parameters: Dict[str, Any] = {}
            updated_delay = 0.0
            for i in range(form_layout.rowCount()):
                widget_item = form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
                if widget_item is not None:
                    widget = widget_item.widget()
                    parameter_name = widget.property("parameter_name")
                    if parameter_name:
                        # Prevent adding delay directly to the parameters dictionary, bad things will happen : )
                        if parameter_name == DELAY_KEYWORD:
                            updated_delay = UIComponentFactory.extract_value(widget)
                            continue
                        else:
                            parameters[parameter_name] = (
                                UIComponentFactory.extract_value(widget)
                            )

            # Create a Task instance directly using the collected parameters.
            task = Task(
                task=original_step.task,
                description=original_step.description,
                delay=updated_delay,
                parameters=parameters,
            )
            tasks.append(task)

        # Create the Experiment instance with the collected tasks.
        try:
            experiment = Experiment(name=experiment_name, steps=tasks)
        except ValidationError as e:
            # Handle validation errors for the experiment.
            QMessageBox.critical(self, "Validation Error", str(e))
            logger.error(f"Error: {e}")
            logger.error(f"{traceback.format_exc()}")
        return experiment

    def getConfiguration(self) -> Experiment:
        """
        Collects the user-modified configuration from the UI and performs validation.

        Extracts data from the UI, validates it, and raises an error
        if validation fails. Otherwise, returns the validated configuration.

        Raises:
            ValueError: If validation of the user-modified configuration fails.
        """
        # Extract the user-modified configuration from the UI elements
        updated_experiment = self.getUserData()
        return updated_experiment

    def get_function(self, task: Task) -> object | None:
        """
        Retrieves the function associated with a specific task name.

        Looks up the function from the provided dictionary or returns None if not found.

        Args:
            task: The name of the task.

        Returns:
            The function associated with the task or None if not found.
        """
        return self.validator.get_function_to_validate(task)

    def generate_experiment_summary(self, data: Experiment):
        if not data:
            return "No experiment configuration loaded."

        experiment_name = data.name
        steps = data.steps

        summary_lines = [f"Experiment: {experiment_name}\n\nSteps Summary:"]

        for i, step in enumerate(steps, 1):
            task_name = step.task
            description = step.description
            summary_lines.append(
                f"  Step {i}: {task_name} - {description if description else 'no description given'}"
            )

        return "\n".join(summary_lines)

    def saveConfiguration(self, config_path: str) -> bool:
        """
        Saves the user-modified experiment configuration to a YAML file.

        Extracts the configuration data from the UI, performs validation,
        and saves it to the specified file path if valid. Displays relevant
        messages based on the success or failure of the operation.

        Args:
            config_path: The path to the YAML file to save the configuration to.

        Returns:
            A boolean indicating whether the configuration was saved successfully.
        """

        config = self.getConfiguration()
        try:
            with open(config_path, "w") as file:
                yaml.dump(config, file, sort_keys=False)
            QMessageBox.information(
                self, "Success", "Configuration saved successfully."
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save configuration: {str(e)}"
            )
