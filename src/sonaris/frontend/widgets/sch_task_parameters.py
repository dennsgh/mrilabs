import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget

from sonaris.frontend.widgets.ui_factory import (  # Assuming custom import, details unknown
    UIComponentFactory,
)
from sonaris.utils.log import get_logger

logger = get_logger()


class TaskParameterConfiguration(QWidget):
    """
    A class to dynamically configure and display UI components based on task parameters.

    Attributes:
        task_dictionary (Dict[str, Dict[str, Callable]]): A mapping of device names to tasks,
            where each task is represented by a function defining its parameters.
        task_enum (Optional[Any]): An optional enumeration to categorize tasks. The exact type
            is not specified, allowing for flexibility in task categorization.
        widget_cache (Dict[Tuple[str, str], QWidget]): A cache to store generated UI components
            for quick retrieval, avoiding redundant UI construction.
        stacked_widget (QStackedWidget): A widget that can stack multiple child widgets, showing one at a time.
        main_layout (QVBoxLayout): The main layout for arranging child widgets vertically.
    """

    def __init__(
        self,
        task_dictionary: Dict[str, Dict[str, Callable]],
        parent: Optional[QWidget] = None,
        task_enum: Optional[Any] = None,
        input_callback: Callable = None,
    ) -> None:
        super().__init__(parent)
        self.input_callback = input_callback
        self.updated_config: dict = None
        self.task_dictionary: Dict[str, Dict[str, Callable]] = task_dictionary
        self.task_enum: Optional[Any] = task_enum
        self.widget_cache: Dict[Tuple[str, str], QWidget] = {}
        self.initUI()

    def initUI(self):
        self.stacked_widget = QStackedWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.stacked_widget)
        self.setLayout(self.main_layout)

    def updateUI(self, device: str, task_name: str) -> None:
        """
        Updates the UI to display the configuration for the specified device and task.

        Args:
            device (str): The name of the device for which the UI should be updated.
            task_name (str): The name of the task for which the UI should be updated.
        """
        cache_key: Tuple[str, str] = (device, task_name)
        if cache_key not in self.widget_cache:
            task_func: Optional[Callable] = self.task_dictionary.get(device, {}).get(
                task_name
            )
            spec: List[QWidget] = self._infer_ui_spec_from_function(task_func)
            container_widget: QWidget = self.generateUI(spec)
            self.widget_cache[cache_key] = container_widget
            self.stacked_widget.addWidget(container_widget)

        index: int = self.stacked_widget.indexOf(self.widget_cache[cache_key])
        self.stacked_widget.setCurrentIndex(index)

    def _infer_ui_spec_from_function(self, task_function: Callable) -> List[QWidget]:
        """
        Infers the UI specification from a function's parameters to generate appropriate widgets.

        Args:
            func (Callable): The function from which to infer UI components.

        Returns:
            List[QWidget]: A list of widgets that correspond to the function's parameters.
        """
        spec: List[QWidget] = []
        sig = inspect.signature(task_function)
        param_types = {name: param.annotation for name, param in sig.parameters.items()}
        # Get metadata from functions
        parameter_annotations = getattr(task_function, "parameter_annotations", {})
        parameter_constraints = getattr(task_function, "parameter_constraints", {})
        for param, expected_type in param_types.items():
            constraints = parameter_constraints.get(param)
            param_annotation = parameter_annotations.get(param, "")

            widget_spec = UIComponentFactory.create_widget(
                param, None, expected_type, constraints, self.input_callback
            )
            # Include parameter name and type in the spec
            spec.append((param, widget_spec, expected_type, param_annotation))
        return spec

    def generateUI(self, spec: List[QWidget]) -> QWidget:
        """
        Generates a UI container with widgets based on the provided specification.

        Args:
            spec (List[QWidget]): A list of widget specifications to include in the UI.

        Returns:
            QWidget: A container widget with the specified UI components.
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        for parameter_name, widget, expected_type, param_annotation in spec:
            # Create a horizontal layout for each parameter
            param_layout = QHBoxLayout()

            # Create a label for each parameter that displays its name and type
            label_text = (
                f"{parameter_name}: {expected_type.__name__}"
                if expected_type
                else parameter_name
            )
            # Append annotation to the label text if it exists
            if param_annotation:
                label_text += f" ({param_annotation})"
            param_label = QLabel(label_text)

            # Add label and widget to the horizontal layout
            param_layout.addWidget(param_label)
            param_layout.addWidget(widget)

            # Add the horizontal layout to the main vertical layout
            layout.addLayout(param_layout)
        container.setLayout(layout)
        return container

    def getUserData(self) -> Dict[str, Any]:
        """
        Retrieves user input data from the current UI configuration.

        Args:
            task_spec (List[Dict[str, Any]]): A specification of the task for which to collect input data.

        Returns:
            Dict[str, Any]: A dictionary containing the collected input data.
        """
        self.updated_config: Dict[str, Any] = {}
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            for widget in current_widget.findChildren(QWidget):
                parameter_name = widget.property("parameter_name")
                if parameter_name:
                    self.updated_config[parameter_name] = (
                        UIComponentFactory.extract_value(widget)
                    )

    def getConfiguration(self) -> Dict[str, Any]:
        """
        Collects the validated configuration from the UI and prepares it for use or saving.

        Args:
            device (str): The device name for which to collect the configuration.
            task_name (str): The task name for which to collect the configuration.

        Returns:
            Dict[str, Any]: A dictionary containing the validated configuration.
        """
        self.getUserData()
        return self.updated_config
