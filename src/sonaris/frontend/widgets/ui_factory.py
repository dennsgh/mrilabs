from typing import Any, Callable, Tuple, Type

from PyQt6.QtCore import pyqtBoundSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QSpinBox,
    QWidget,
)

from sonaris.defaults import DECIMAL_POINTS


class UIComponentFactory:

    TRUTH_VALUES = [
        "true",
        "1",
        "on",
        "ok",
        "yes",
        "resume",
        "continue",
    ]
    FALSE_VALUES = [
        "false",
        "0",
        "off",
        "no",
        "cancel",
        "abort",
        "deny",
    ]

    SIGNAL_MAP = {
        QLineEdit: "textChanged",
        QSpinBox: "valueChanged",
        QDoubleSpinBox: "valueChanged",
        QComboBox: "currentIndexChanged",
        QCheckBox: "stateChanged",
    }

    @staticmethod
    def create_widget(
        parameter_name: str,
        value: Any,
        expected_type: type,
        constraints: Any,
        callback: Callable = None,
    ) -> QWidget:
        """
        Creates a widget based on the parameter's expected type and the specific constraints.
        """
        widget, default_value = UIComponentFactory.map_type_to_widget(
            expected_type, constraints
        )

        # Apply the current value or default to the widget
        if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.setValue(
                expected_type(value)
                if value is not None
                else expected_type(default_value)
            )
        elif isinstance(widget, QCheckBox):
            widget.setChecked(
                value if value is not None else expected_type(default_value)
            )
        elif isinstance(widget, QComboBox):
            if expected_type == bool:
                # Handle boolean parameters differently
                if isinstance(value, str):
                    index = UIComponentFactory.findTextIndexForBooleanValue(
                        widget, value
                    )
                    widget.setCurrentIndex(index)
                elif isinstance(value, bool):
                    # Convert boolean to string representation to find the index
                    value_str = "true" if value else "false"
                    index = UIComponentFactory.findTextIndexForBooleanValue(
                        widget, value_str
                    )
                    widget.setCurrentIndex(index)
            elif value in constraints:  # Assuming `constraints` is a list for QComboBox
                index = widget.findData(value)
                widget.setCurrentIndex(index)
            else:
                widget.setCurrentIndex(0)
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value) if value is not None else str(default_value))
        widget.setProperty("expected_type", expected_type.__name__)
        widget.setProperty("parameter_name", parameter_name)
        if callback:
            UIComponentFactory.connect_widget_signal(widget, callback)
        return widget

    @staticmethod
    def findTextIndexForBooleanValue(widget: QComboBox, value: str) -> int:
        # Normalize the string value for comparison
        normalized_value = value.lower()
        # Determine if the value is considered true or false
        if normalized_value in UIComponentFactory.TRUTH_VALUES:
            truthy = True
        elif normalized_value in UIComponentFactory.FALSE_VALUES:
            truthy = False
        else:
            return 0  # Default to the first index if undetermined

        # Iterate through the combo box items to find the match
        for i in range(widget.count()):
            item_text = widget.itemText(i).lower()
            if (truthy and item_text in UIComponentFactory.TRUTH_VALUES) or (
                not truthy and item_text in UIComponentFactory.FALSE_VALUES
            ):
                return i
        return 0  # Default to the first index if no match found

    @staticmethod
    def map_type_name_to_type(type_name: str):
        """
        Maps a type name (string) back to a type. This is needed for casting values fetched from UI components.
        """
        return {
            "bool": bool,
            "int": int,
            "float": float,
            "str": str,
        }.get(
            type_name, None
        )  # Default to str if not found

    @staticmethod
    def map_type_to_widget(
        param_type: type, constraints: Any = None
    ) -> Tuple[QWidget, Any]:
        """
        Maps a parameter type to a PyQt widget, considering the constraints.
        """
        if param_type in [int, float, str, bool] and isinstance(constraints, list):
            widget = QComboBox()
            for value in constraints:
                widget.addItem(str(value), value)
            default_value = constraints[0]
        elif param_type == int:
            widget = QSpinBox()
            if constraints and isinstance(constraints, tuple):
                widget.setMinimum(constraints[0])
                widget.setMaximum(constraints[1])
            else:
                widget.setRange(-2147483648, 2147483647)  # Default 32-bit integer range
            default_value = 0

        elif param_type == float:
            widget = QDoubleSpinBox()
            widget.setDecimals(DECIMAL_POINTS)
            if constraints and isinstance(constraints, tuple):
                widget.setMinimum(constraints[0])
                widget.setMaximum(constraints[1])
            else:
                widget.setRange(-1.0e100, 1.0e100)
                # Default to 3 decimal places for broad applicability
            default_value = 0.0

        elif param_type == str:
            widget = QLineEdit()
            # Optionally set a placeholder text here to guide the user
            default_value = ""

        elif param_type == bool:
            widget = QCheckBox()
            default_value = False
        else:  # Default case, especially for types like str without specific constraints
            widget = QLineEdit()
            default_value = ""

        # Set property to identify the expected type easily
        return widget, default_value

    @staticmethod
    def connect_widget_signal(widget: QWidget, callback: Callable[[Any], None]) -> None:
        """
        Connects the appropriate signal of the widget to the given callback function.

        Args:
            widget: The widget whose signal needs to be connected.
            callback: The callback function to be called when the signal is emitted.
        """
        widget_class: Type[QWidget] = type(widget)  # Get the class of the widget
        if widget_class in UIComponentFactory.SIGNAL_MAP:
            signal_name: str = UIComponentFactory.SIGNAL_MAP[widget_class]
            signal: pyqtBoundSignal = getattr(widget, signal_name)
            signal.connect(callback)
        else:
            raise ValueError("Unsupported widget type for signal connection")

    @staticmethod
    def extract_value(widget: QWidget, cast_type: type = None) -> Any:
        """Extracts and returns the value from the widget, casting it to the expected type."""
        if cast_type is None:
            cast_type = UIComponentFactory.map_type_name_to_type(
                widget.property("expected_type")
            )

        # From here cast_type is determined
        if isinstance(widget, QLineEdit):
            value = widget.text()
        elif isinstance(widget, QCheckBox):
            value = widget.isChecked()
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            value = widget.value()
        elif isinstance(widget, QComboBox):
            value = widget.currentData()
        else:
            value = None

        # Special handling for boolean cast_type
        if cast_type == bool:
            if isinstance(value, str):
                # Normalize the string to lower case to simplify comparisons
                return value.lower() in UIComponentFactory.TRUTH_VALUES
            else:
                return bool(
                    value
                )  # Directly cast to bool for non-string values depending of Pythonic truthiness
        elif cast_type in [int, float, str]:
            return cast_type(value) if cast_type else None
        return value if value else None
