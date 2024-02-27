import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget
from widgets.ui_factory import (  # Assuming custom import, details unknown
    UIComponentFactory,
)


class ParameterConfiguration(QWidget):
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
    ) -> None:
        super().__init__(parent)
        self.task_dictionary: Dict[str, Dict[str, Callable]] = task_dictionary
        self.task_enum: Optional[Any] = task_enum
        self.widget_cache: Dict[Tuple[str, str], QWidget] = {}
        self.stacked_widget: QStackedWidget = QStackedWidget(self)
        self.main_layout: QVBoxLayout = QVBoxLayout(self)
        self.main_layout.addWidget(self.stacked_widget)
        self.setLayout(self.main_layout)

    def updateUI(self, device: str, task_name: str) -> None:
        """
        Updates the UI to display the configuration for the specified device and task.

        Args:
            device (str): The name of the device for which the UI should be updated.
            task_name (str): The name of the task for which the UI should be updated.
        """
        print(f"Got{device}-{task_name}")
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
        param_constraints = getattr(task_function, "param_constraints", {})
        for param, expected_type in param_types.items():
            constraints = param_constraints.get(param)
            widget_spec = UIComponentFactory.create_widget(
                param, None, expected_type, constraints
            )
            # Include parameter name and type in the spec
            spec.append((param, widget_spec, expected_type))
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
        for param_name, widget, expected_type in spec:
            # Create a label for each parameter that displays its name and type
            label_text = (
                f"{param_name}: {expected_type.__name__}"
                if expected_type
                else param_name
            )
            param_label = QLabel(label_text)
            layout.addWidget(param_label)
            layout.addWidget(widget)
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
        parameters: Dict[str, Any] = {}
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            for widget in current_widget.findChildren(QWidget):
                param_name = widget.property("param_name")
                if param_name:
                    expected_type = UIComponentFactory.map_type_name_to_type(
                        widget.property("expected_type")
                    )
                    parameters[param_name] = UIComponentFactory.extract_value(
                        widget, expected_type
                    )
        return parameters

    def getConfiguration(self) -> Dict[str, Any]:
        """
        Collects the validated configuration from the UI and prepares it for use or saving.

        Args:
            device (str): The device name for which to collect the configuration.
            task_name (str): The task name for which to collect the configuration.

        Returns:
            Dict[str, Any]: A dictionary containing the validated configuration.
        """
        # TODO: validation
        return self.getUserData()
