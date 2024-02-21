from enum import Enum
from typing import Callable, Dict

import yaml
from features.task_validator import validate_configuration
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ParameterConfiguration(QWidget):
    def __init__(self, task_dictionary, parent=None):
        super().__init__(parent)
        self.task_dictionary = task_dictionary
        self.widget_cache = {}  # Cache for configurations
        self.stacked_widget = QStackedWidget(self)  # Use QStackedWidget to manage UIs
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(
            self.stacked_widget
        )  # Add the stacked widget to the main layout

    def updateUI(self, device, task_name):
        cache_key = (device, task_name)
        if cache_key not in self.widget_cache:
            print(f"Creating {device} - {task_name}")
            spec = self.task_dictionary.get(device, {}).get(task_name, [])
            container_widget = self.generateUI(spec)
            self.widget_cache[cache_key] = container_widget
            self.stacked_widget.addWidget(
                container_widget
            )  # Add new configuration to stacked widget

        # Switch to the relevant configuration
        self.stacked_widget.setCurrentWidget(self.widget_cache[cache_key])

    def createComponent(self, component, layout):
        # Adjust this method to add widgets to the passed layout
        if component["type"] == "QComboBox":
            comboBox = QComboBox(self)
            options = component.get("options", [])
            comboBox.addItems(options)
            if "default" in component:
                default_index = (
                    options.index(component["default"])
                    if component["default"] in options
                    else 0
                )
                comboBox.setCurrentIndex(default_index)
            layout.addWidget(QLabel(component["label"]))  # Add to the passed layout
            layout.addWidget(comboBox)  # Add to the passed layout
        elif component["type"] == "QLineEdit":
            lineEdit = QLineEdit(self)
            if "default" in component:
                lineEdit.setText(str(component["default"]))
            layout.addWidget(QLabel(component["label"]))  # Add to the passed layout
            layout.addWidget(lineEdit)  # Add to the passed layout
        # Implement other component types as needed

    def generateUI(self, spec):
        container = QWidget()  # Container for this set of parameters
        layout = QVBoxLayout(container)

        for component in spec:
            self.createComponent(
                component, layout
            )  # Pass the layout to createComponent

        container.setLayout(layout)
        return container

    def get_parameters(self, task_spec):
        parameters = {}
        current_container = (
            self.stacked_widget.currentWidget()
        )  # Get the currently visible container
        if not current_container:
            return parameters  # Return empty if no container is visible

        for spec in task_spec:
            kwarg_label = spec.get("kwarg_label", spec.get("label"))
            # Now iterate through the current container's layout to find the widget
            layout = current_container.layout()
            for i in range(layout.count()):
                layout_item = layout.itemAt(i)
                widget = layout_item.widget()
                if isinstance(widget, QLabel) and widget.text() == spec["label"]:
                    # Assuming input widget is next in the layout after its label
                    input_widget = (
                        layout.itemAt(i + 1).widget()
                        if i + 1 < layout.count()
                        else None
                    )
                    if input_widget:
                        value = self.extract_value(input_widget, spec)
                        if value is not None:  # Only add if extraction was successful
                            parameters[kwarg_label] = value
                    break  # Break after finding the widget to avoid unnecessary iterations

        return parameters

    def extract_value(self, widget, spec):
        if isinstance(widget, QLineEdit):
            value = widget.text()
        elif isinstance(widget, QComboBox):
            value = widget.currentText()
        else:
            value = None

        # Correctly cast the value based on its data type
        if spec.get("data_type") == "int":
            try:
                return int(value)
            except ValueError:
                # Handle invalid int conversion
                return None
        elif spec.get("data_type") == "float":
            try:
                return float(value)
            except ValueError:
                # Handle invalid float conversion
                return None
        elif spec.get("data_type") == "str":
            return str(value)
        elif spec.get("data_type") == "bool":
            # Assuming that boolean values are represented by specific strings (e.g., "ON" or "OFF")
            return value.lower() in ["on", "true", "1"]
        else:
            return value


class ExperimentConfiguration(QWidget):
    def __init__(
        self,
        parent=None,
        task_functions: Dict[str, Callable] = None,
        task_enum: Enum = None,
    ):
        super().__init__(parent)
        self.task_functions =   task_functions  
        
        self.config: dict = None
        self.initUI()
        self.task_enum = task_enum
    def createTaskForm(self, task):
        formWidget = QWidget()
        formLayout = QFormLayout()
        formWidget.setLayout(formLayout)

        for param, value in task.get("parameters", [{}])[0].items():
            if isinstance(value, bool):
                checkBox = QCheckBox()
                checkBox.setChecked(value)
                formLayout.addRow(QLabel(param), checkBox)
            elif isinstance(value, int):
                spinBox = QSpinBox()
                spinBox.setValue(value)
                formLayout.addRow(QLabel(param), spinBox)
            # Add more widgets for different data types as needed

        return formWidget

    def addValidation(self, lineEdit):
        lineEdit.textChanged.connect(self.validateInput)

    def addHelpButton(self, paramName, formLayout, row):
        helpBtn = QPushButton("?")
        helpBtn.clicked.connect(lambda: self.showParamHelp(paramName))
        formLayout.setWidget(row, QFormLayout.ItemRole.FieldRole, helpBtn)

    def showParamHelp(self, paramName):
        # Show a QMessageBox with information about the parameter
        QMessageBox.information(self, "Parameter Help", f"Help for {paramName}")

    def validateInput(self, text):
        # Dummy validation logic
        if not text:
            self.setStyleSheet("border: 1px solid red;")
        else:
            self.setStyleSheet("")

    def initUI(self):
        self.layout = QVBoxLayout(self)
        self.tabWidget = QTabWidget(self)
        self.layout.addWidget(self.tabWidget)
        self.descriptionWidget = QTextEdit(self)
        self.descriptionWidget.setReadOnly(True)
        self.descriptionWidget.setText(
            "Load an experiment configuration to see its details here."
        )
        self.layout.addWidget(self.descriptionWidget)

    def loadConfiguration(self, config_path):
        try:
            with open(config_path, "r") as file:
                self.config = yaml.safe_load(file)
            self.validate_and_display()
            return True, "OK"
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load or parse the configuration: {str(e)}"
            )
            self.descriptionWidget.setText("Failed to load or parse the configuration.")
        return False, "Failed to load or parse the configuration"

    def validate_and_display(self):
        if not self.config:
            QMessageBox.warning(self, "Error", "No configuration loaded.")
            return

        # Perform validation
        validation_results = validate_configuration(
            self.config, self.task_functions, self.task_enum
        )

        # Initialize a flag to track overall validation status
        overall_valid = True
        messages = []

        # Process validation results
        for task_name, is_valid, message in validation_results:
            if not is_valid:
                overall_valid = False
                messages.append(f"{task_name}: {message}")

        # Update UI based on validation results
        if not overall_valid:
            QMessageBox.warning(
                self, "Configuration Validation Failed", "\n".join(messages)
            )
            self.descriptionWidget.setText(
                "Configuration validation failed:\n" + "\n".join(messages)
            )
        else:
            self.displayExperimentDetails()

        # Return the overall validation status and concatenated messages
        return overall_valid, "\n".join(messages)

    def displayExperimentDetails(self):
        details = "Experiment Overview:\n"
        for step in self.config.get("experiment", {}).get("steps", []):
            details += f"\nTask: {step.get('task')} - {step.get('description', 'No description')}"
            for param in step.get("parameters", [{}])[0].items():
                details += f"\n - {param[0]}: {param[1]}"
        self.descriptionWidget.setText(details)

    def get_configuration(self):
        """
        Return the validated configuration for scheduling.
        This method should be called after loadConfiguration and validate_configuration to ensure data is valid.
        """
        if self.config:
            steps = self.config.get("experiment", {}).get("steps", [])
            return steps
        else:
            return []
