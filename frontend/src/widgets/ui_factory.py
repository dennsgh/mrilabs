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
    def getDefaultValue(param_name: str, expected_type: type) -> Any:
        # Example default value logic based on type or name
        default_values = {
            "frequency": 1.0,  # Default frequency in Hz
            "amplitude": 0.5,  # Default amplitude in V
        }
        if expected_type is int:
            return 0
        elif expected_type is float:
            return 0.0
        elif expected_type is bool:
            return False
        elif expected_type is str:
            return ""
        elif expected_type is list:
            return []
        elif expected_type is dict:
            return {}
        return default_values.get(param_name, None)

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
            type_name, str
        )  # Default to str if not found

    @staticmethod
    def map_type_to_widget(
        param_type: type, constraints: Any = None
    ) -> Tuple[QWidget, Any]:
        """
        Maps a parameter type to a PyQt widget, considering the constraints.
        """
        if param_type in [int, float, str] and isinstance(constraints, list):
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
    def extract_value(widget, expected_type=None):
        """Extracts and returns the value from the widget, casting it to the expected type."""
        if expected_type is None:
            expected_type_name = widget.property("expected_type")
            if expected_type_name == "bool":
                expected_type = bool
            elif expected_type_name == "int":
                expected_type = int
            elif expected_type_name == "float":
                expected_type = float
            elif expected_type_name == "str":
                expected_type = str
            else:
                expected_type = None

        if isinstance(widget, QLineEdit):
            value = widget.text()
        elif isinstance(widget, QCheckBox):
            value = widget.isChecked()
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            value = widget.value()
        elif isinstance(widget, QComboBox):
            value = (
                widget.currentData()
            )  # Or use currentText(), depending on what's expected
        else:
            value = None

        if expected_type in [bool, int, float, str]:
            return expected_type(value)
        return value
