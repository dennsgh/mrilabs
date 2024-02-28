import inspect
from enum import Enum

import yaml
from features.task_validator import (
    get_function_to_validate,
    get_task_enum_value,
    validate_configuration,
)
from header import ErrorLevel
from PyQt6.QtWidgets import (
    QFormLayout,
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
        self.task_functions = task_functions
        self.task_enum = task_enum
        self.config: dict[str, object] | None = None
        self.initUI()

    def initUI(self) -> None:
        """
        Initializes the user interface of the widget.
        """
        self.main_layout = QVBoxLayout(self)
        self.tabWidget = QTabWidget(self)
        self.main_layout.addWidget(self.tabWidget)

        self.descriptionWidget = QTextEdit(self)
        self.descriptionWidget.setReadOnly(True)
        self.descriptionWidget.setText(
            "Load an experiment configuration to see its details here."
        )
        self.main_layout.addWidget(self.descriptionWidget)
        # Set size policy to make sure the widget expands both horizontally and vertically
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tabWidget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    def loadConfiguration(self, config_path):
        valid, message, descriptionText = self.load_and_validate(config_path)
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
        messages = (
            []
        )  # This will accumulate our error messages in a more compact format

        for task_name, is_valid, message, error_level in validation_results:
            if not is_valid:
                overall_valid = False
                # Update the highest error level based on the current error
                if error_level.value > highest_error_level.value:
                    highest_error_level = error_level
            # Append the task and its message in a compact manner
            messages.append(f"{task_name}: {message}")

        # Join messages with a separator that puts each on a new line but in a more compact form
        compact_message = "\n".join(messages)

        return overall_valid, compact_message, highest_error_level

    def error_handling(
        self, overall_valid: bool, messages: list[str], highest_error_level: ErrorLevel
    ) -> str:
        """
        Handles display of error messages and configuration summaries based on validation results.

        Displays appropriate messages based on the overall validity and error level.

        Args:aining either a summary of the configuration or an error message.
        """
        if overall_valid or highest_error_level == ErrorLevel.INFO:
            descriptionText = self.generate_experiment_summary(self.config)
        else:
            descriptionText = (
                "OK"  # Default message, will be overwritten by error cases below
            )

        # Handle different levels of error messages
        if highest_error_level == ErrorLevel.BAD_CONFIG:
            QMessageBox.warning(
                self, "Configuration Validation Issues", "".join(messages)
            )
            descriptionText = "Configuration Validation Issues: \n" + "".join(messages)
        elif highest_error_level == ErrorLevel.INVALID_YAML:
            QMessageBox.critical(
                self, "Configuration Validation Failed", "".join(messages)
            )
            descriptionText = "Configuration Validation Failed: \n" + "".join(messages)
        return descriptionText

    def load_and_validate(self, config_path: str) -> None:
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
            return

        overall_valid, messages, highest_error_level = self.validate(self.config)
        # Initialize description text with a default message or an experiment summary
        # Generate a summary if the config is valid or if only INFO level messages are present
        descriptionText = self.error_handling(
            overall_valid, messages, highest_error_level
        )

        return overall_valid, "\n".join(messages), descriptionText

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
            param_constraints = getattr(task_function, "param_constraints", {})
            # Initialize a dictionary to store the task parameters from the configuration
            task_parameters = task.get("parameters", {})

            # trunk-ignore(ruff/B007)
            for param_name, param in sig.parameters.items():
                value = task_parameters.get(param_name, None)
                expected_type = param_types.get(param_name, str)

                # Now, extract specific constraints for the current parameter
                specific_constraints = param_constraints.get(param_name, None)

                widget = UIComponentFactory.create_widget(
                    param_name, value, expected_type, specific_constraints
                )
                widget.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
                )
                # Create labels for parameter name and type hinting (optional)
                paramNameLabel = QLabel(f"{param_name} :{expected_type.__name__}")
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
        """
        Collects the configuration data from the UI, extracting and validating user input.

        Iterates through each tab and form layout, extracting form widget values
        and converting them to the expected data types based on the defined parameter types.

        Raises a ValueError if validation fails.

        Returns:
            A dictionary containing the updated experiment configuration data.
        """
        updated_config = {
            "experiment": {
                "name": self.config.get("experiment", {}).get(
                    "name", "Unnamed Experiment"
                ),
                "steps": [],
            }
        }

        for index in range(self.tabWidget.count()):
            step_widget = self.tabWidget.widget(index)
            original_step = self.config["experiment"]["steps"][index]

            updated_step = original_step.copy()
            updated_parameters = {}

            # Extract the QWidget that holds the form layout for the current step
            form_widget = step_widget.findChild(QScrollArea).widget()
            form_layout = form_widget.layout()

            # Reconstruct the parameters from UI components
            for i in range(form_layout.rowCount()):
                row_widget = form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
                if row_widget:
                    param_label_widget = row_widget.widget()
                    param_name = param_label_widget.text().split(" :")[
                        0
                    ]  # Extract parameter name before the colon

                    input_widget = form_layout.itemAt(
                        i, QFormLayout.ItemRole.FieldRole
                    ).widget()
                    param_value = UIComponentFactory.extract_value(input_widget)
                    if param_value is None:  # None indicates it wasn't recognized.
                        continue

                    updated_parameters[param_name] = param_value

            updated_step["parameters"] = updated_parameters
            updated_config["experiment"]["steps"].append(updated_step)

        return updated_config

    def getConfiguration(self) -> dict:
        """
        Collects the user-modified configuration from the UI and performs validation.

        Extracts data from the UI, validates it, and raises an error
        if validation fails. Otherwise, returns the validated configuration.

        Raises:
            ValueError: If validation of the user-modified configuration fails.
        """
        # Extract the user-modified configuration from the UI elements
        data = self.getUserData()

        # Validate the extracted data
        overall_valid, messages, highest_error_level = self.validate(data)
        descriptionText = self.error_handling(
            overall_valid, messages, highest_error_level
        )
        if not overall_valid:
            self.descriptionWidget.setText(descriptionText)
            raise ValueError("Configuration validation failed.")

        return data

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

    def validate_and_convert_value(self, text, expected_type):
        """
        Validates and converts text input to the expected data type.
        Raises ValueError if the value is invalid.
        """

        if expected_type == bool:
            # Specific logic for converting text to bool
            return text.lower() in ["true", "1", "t", "y", "yes", "ok", "on"]
        elif expected_type in (int, float):
            if expected_type == int:
                return int(text)
            else:
                return float(text)
        else:
            return text  # Return as string by default

    def generate_experiment_summary(self, data: dict):
        """
        Generates a summary of the experiment based on the YAML configuration.
        This is a placeholder function; you should replace the logic with actual
        processing of your specific YAML structure to extract and format the summary.
        """
        # Pseudocode for generating a summary - replace with actual implementation
        experiment_name = data.get("experiment_name", "Unnamed Experiment")
        parameters = data.get("parameters", {})
        objectives = data.get("objectives", [])

        summary_lines = [
            f"Experiment: {experiment_name}",
            "Parameters:",
        ]
        for param, value in parameters.items():
            summary_lines.append(f"  - {param}: {value}")

        summary_lines.append("Objectives:")
        for objective in objectives:
            summary_lines.append(f"  - {objective}")

        return "".join(summary_lines)

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
