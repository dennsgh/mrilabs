from enum import Enum
from typing import Any, Tuple

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QSpinBox,
    QWidget,
)


class UIComponentFactory:
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
            widget.setDecimals(7)
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
    def create_widget(
        parameter_name: str, value: Any, expected_type: type, constraints: Any
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
            if value in constraints:  # Assuming `constraints` is a list for QComboBox
                index = widget.findData(value)
                widget.setCurrentIndex(index)
            else:
                widget.setCurrentIndex(0)
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value) if value is not None else str(default_value))
        widget.setProperty("expected_type", expected_type.__name__)
        widget.setProperty("parameter_name", parameter_name)

        return widget

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
                return value.lower() in [
                    "true",
                    "1",
                    "on",
                    "ok",
                    "yes",
                ]  # Returns True for these cases, False otherwise
            else:
                return bool(
                    value
                )  # Directly cast to bool for non-string values depending of Pythonic truthiness
        elif cast_type in [int, float, str]:
            return cast_type(value) if cast_type else None
        return value if value else None
