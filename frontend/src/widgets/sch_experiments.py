import inspect
from enum import Enum
from typing import Callable

import yaml
from features.task_validator import (
    get_function_to_validate,
    get_task_enum_value,
    validate_configuration,
)
from header import ErrorLevel
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
from widgets.ui_factory import UIComponentFactory


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
    ) -> None:
        """
        Initializes the widget.

        Args:
            parent: The parent widget of this widget. Defaults to None.
            task_functions: A dictionary mapping task names to their corresponding functions. Defaults to None.
            task_enum: An enumeration representing the valid task types. Defaults to None.
        """
        super().__init__(parent)
        self.task_functions: dict[str, Callable] = task_functions
        self.task_enum: Enum = task_enum
        self.config: dict[str, object] | None = None
        self.updated_config: dict = None
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
        # Automatically grab the current tab index if needed or work with the updated_config
        currentTabIndex = self.tabWidget.currentIndex()
        if currentTabIndex != -1:
            self.getUserData()  # Ensure the updated_config is current
            step_config = self.updated_config["experiment"]["steps"][currentTabIndex]
            yamlStr = yaml.dump(step_config, sort_keys=False)
            self.yamlDisplayWidget.setText(yamlStr)

    def loadConfiguration(self, config_path):
        valid, message, descriptionText = self.loadValidate(config_path)
        self.descriptionWidget.setText(descriptionText)

        if valid:
            self.displayExperimentDetails()
            self.update()
            return True, "Configuration loaded successfully."
        else:
            return False, "Failed to load or parse the configuration."

    def validate(self, data: dict) -> tuple[bool, list[str], ErrorLevel]:
        """
        Validates the provided experiment configuration data.

        Checks for various errors and inconsistencies in the configuration based on pre-defined rules.

        Args:
            data: The experiment configuration data in dictionary format.

        Returns:
            A tuple containing three elements:
                - A boolean indicating whether the configuration is valid.
                - A list of error messages if the configuration is invalid.
                - The highest encountered error level (INFO, BAD_CONFIG, INVALID_YAML).
        """
        overall_valid = True
        highest_error_level = ErrorLevel.INFO  # Assume the lowest severity to start
        validation_results = validate_configuration(
            data, self.task_functions, self.task_enum
        )
        message_dict = {"errors": [], "warnings": [], "infos": []}
        for task_name, is_valid, message, error_level in validation_results:
            if not is_valid:
                overall_valid = False
                if error_level.value > highest_error_level.value:
                    highest_error_level = error_level
                message_dict["errors"].append(f"{task_name}: {message}")
            else:
                # Check if message contains more than just "Validation issues: "
                if message.strip() != "Validation issues:":
                    message_dict["infos"].append(f"{task_name}: {message}")

        return overall_valid, message_dict, highest_error_level

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
                self.generate_experiment_summary(self.config) + "\n" + descriptionText
            )

        return descriptionText

    def loadValidate(self, config_path: str) -> None:
        """
        Loads and displays an experiment configuration or handles any errors encountered.

        Performs loading, validation, and displays the results or error messages.

        Args:
            config_path: The path to the YAML file containing the configuration.
        """
        with open(config_path, "r") as file:
            self.config = yaml.safe_load(file)
        if not self.config:
            QMessageBox.warning(self, "Error", "No configuration loaded.")
            return False, "No configuration loaded.", {}

        overall_valid, message_dict, highest_error_level = self.validate(self.config)
        descriptionText = self.errorHandling(
            overall_valid, message_dict, highest_error_level
        )

        return overall_valid, message_dict, descriptionText

    def displayExperimentDetails(self) -> None:
        """
        Displays the details of the loaded experiment configuration in a tabbed interface.

        Creates tabs for each step in the experiment and populates them with
        widgets for interacting with the step parameters.

        Raises a warning message if no configuration is loaded.
        """
        if not self.config:
            QMessageBox.warning(self, "Error", "No configuration loaded.")
            return

        self.tabWidget.clear()
        steps = self.config.get("experiment", {}).get("steps", [])
        if steps:
            for index, step in enumerate(steps, start=1):
                valid, err = self.createTaskTab(step)
                if not valid:
                    QMessageBox.warning(
                        self, "Warning", f"At step {index} [{step}]:{err}"
                    )
        self.layout().update()

    def createTaskTab(self, task: dict) -> bool:
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

        duration = task.get("duration", 0.0)
        durationWidget = UIComponentFactory.create_widget(
            "duration", duration, float, None, self.updateYamlDisplay
        )
        durationWidget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        formLayout.addRow(QLabel("duration (s):"), durationWidget)

        formWidget.setLayout(formLayout)
        try:
            task_function = self.get_function(task.get("task"))
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
            task_parameters = task.get("parameters", {})

            # trunk-ignore(ruff/B007)
            for parameter_name, param in sig.parameters.items():
                value = task_parameters.get(parameter_name, None)
                expected_type = param_types.get(parameter_name, str)
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
                    self.updateYamlDisplay,
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
                tab, get_task_enum_value(task.get("task"), self.task_enum)
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
            return False, f"{e}"

    def getUserData(self) -> dict:
        if self.updated_config is None:
            self.updated_config = {
                "experiment": {
                    "name": self.config.get("experiment", {}).get(
                        "name", "Unnamed Experiment"
                    ),
                    "steps": [],
                }
            }

        self.updated_config["experiment"][
            "steps"
        ].clear()  # Clear existing steps to repopulate

        for index in range(self.tabWidget.count()):
            step_widget = self.tabWidget.widget(index)
            form_widget = step_widget.findChild(QScrollArea).widget()
            form_layout = form_widget.layout()

            original_step: dict = self.config["experiment"]["steps"][index]
            updated_step = original_step.copy()
            updated_parameters = {}

            duration_updated = False

            for i in range(form_layout.rowCount()):
                widget_item = form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
                if widget_item is not None:
                    widget = widget_item.widget()
                    parameter_name = widget.property("parameter_name")
                    if parameter_name:
                        param_value = UIComponentFactory.extract_value(widget)
                        if parameter_name == "duration":
                            updated_step["duration"] = param_value
                            duration_updated = True
                        else:
                            updated_parameters[parameter_name] = param_value

            if not duration_updated:
                updated_step["duration"] = 0  # Default duration if not specified

            updated_step["parameters"] = updated_parameters
            self.updated_config["experiment"]["steps"].append(updated_step)

    def getConfiguration(self) -> dict:
        """
        Collects the user-modified configuration from the UI and performs validation.

        Extracts data from the UI, validates it, and raises an error
        if validation fails. Otherwise, returns the validated configuration.

        Raises:
            ValueError: If validation of the user-modified configuration fails.
        """
        # Extract the user-modified configuration from the UI elements
        self.getUserData()

        # Validate the extracted data
        overall_valid, messages, highest_error_level = self.validate(
            self.updated_config
        )
        descriptionText = self.errorHandling(
            overall_valid, messages, highest_error_level
        )
        if not overall_valid:
            self.descriptionWidget.setText(descriptionText)
            raise ValueError("Configuration validation failed.")

        return self.updated_config

    def get_function(self, task: str) -> object | None:
        """
        Retrieves the function associated with a specific task name.

        Looks up the function from the provided dictionary or returns None if not found.

        Args:
            task: The name of the task.

        Returns:
            The function associated with the task or None if not found.
        """
        return get_function_to_validate(task, self.task_functions, self.task_enum)

    def generate_experiment_summary(self, data: dict):
        if not data or "experiment" not in data:
            return "No experiment configuration loaded."

        experiment_data = data["experiment"]
        experiment_name = experiment_data.get("name", "Unnamed Experiment")
        steps = experiment_data.get("steps", [])

        summary_lines = [f"Experiment: {experiment_name}\n\nSteps Summary:"]

        for i, step in enumerate(steps, 1):
            task_name = step.get("task", "Unknown Task")
            description = step.get("description", "No description provided.")
            summary_lines.append(f"  Step {i}: {task_name} - {description}")

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
