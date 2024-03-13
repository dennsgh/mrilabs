import sys

import pytest
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QSpinBox,
)

from sonaris.frontend.widgets.ui_factory import UIComponentFactory


class TestUIComponentFactory:
    @pytest.fixture(autouse=True)
    def setup_qapp(self):
        # Initialize QApplication to create widgets
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        yield app
        app.quit()

    # Test Cases for extract_value
    def test_extract_value_from_line_edit(self):
        # Test Case: Extracting value from a QLineEdit widget
        line_edit = UIComponentFactory.create_widget(
            "line_edit_param", "Test", str, None
        )
        extracted_value = UIComponentFactory.extract_value(line_edit)
        assert extracted_value == "Test"

    def test_extract_value_from_checkbox(self):
        # Test Case: Extracting value from a QCheckBox widget
        checkbox = UIComponentFactory.create_widget("checkbox_param", True, bool, None)
        extracted_value = UIComponentFactory.extract_value(checkbox)
        assert extracted_value == True

    def test_extract_value_from_spin_boxes(self):
        # Test Case: Extracting value from QSpinBox and QDoubleSpinBox widgets
        spin_box = UIComponentFactory.create_widget("spin_box_param", 10, int, None)
        extracted_int_value = UIComponentFactory.extract_value(spin_box)
        assert extracted_int_value == 10

        double_spin_box = UIComponentFactory.create_widget(
            "double_spin_box_param", 3.14, float, None
        )
        extracted_float_value = UIComponentFactory.extract_value(double_spin_box)
        assert extracted_float_value == 3.14

    def test_extract_value_from_combo_box(self):
        # Test Case: Extracting value from a QComboBox widget
        combo_box = UIComponentFactory.create_widget("combo_box_param", 2, int, [1, 2])
        extracted_value = UIComponentFactory.extract_value(combo_box)
        assert extracted_value == 2

    def test_extract_value_boolean_string_values(self):
        # Test Case: Handling boolean type with string values
        combo_box = UIComponentFactory.create_widget(
            "bool_combo_box_param", None, bool, ["True", "False"]
        )
        combo_box.setCurrentIndex(0)  # Select "True"
        extracted_value_true = UIComponentFactory.extract_value(combo_box)
        assert extracted_value_true == True

        combo_box.setCurrentIndex(1)  # Select "False"
        extracted_value_false = UIComponentFactory.extract_value(combo_box)
        assert extracted_value_false == False

    # Test Cases for create_widget
    def test_create_widget_no_constraints(self):
        # Test Case: Creating widget for int, float, str, and bool types without constraints
        int_widget = UIComponentFactory.create_widget("int_param", None, int, None)
        assert isinstance(int_widget, QSpinBox)

        float_widget = UIComponentFactory.create_widget(
            "float_param", None, float, None
        )
        assert isinstance(float_widget, QDoubleSpinBox)

        str_widget = UIComponentFactory.create_widget("str_param", None, str, None)
        assert isinstance(str_widget, QLineEdit)

        bool_widget = UIComponentFactory.create_widget("bool_param", None, bool, None)
        assert isinstance(bool_widget, QCheckBox)

    def test_create_widget_with_constraints(self):
        # Test Case: Creating widget for int, float, str, and bool types with constraints
        int_widget = UIComponentFactory.create_widget("int_param", None, int, (0, 100))
        assert isinstance(int_widget, QSpinBox)

        float_widget = UIComponentFactory.create_widget(
            "float_param", None, float, (-1.0, 1.0)
        )
        assert isinstance(float_widget, QDoubleSpinBox)

        str_widget = UIComponentFactory.create_widget("str_param", None, str, None)
        assert isinstance(str_widget, QLineEdit)

        bool_widget = UIComponentFactory.create_widget("bool_param", None, bool, None)
        assert isinstance(bool_widget, QCheckBox)

    def test_create_widget_boolean_string_values(self):
        # Test Case: Creating widget for boolean type with string values
        bool_widget = UIComponentFactory.create_widget(
            "bool_param", None, bool, ["True", "False"]
        )
        assert isinstance(bool_widget, QComboBox)

    def test_create_widget_with_annotations(self):
        # Test Case: Creating widget for parameter with annotations
        int_widget = UIComponentFactory.create_widget("int_param", None, int, None)
        assert int_widget.property("expected_type") == "int"

    def test_create_widget_with_default_values(self):
        # Test Case: Handling default values
        int_widget = UIComponentFactory.create_widget("int_param", 10, int, None)
        assert int_widget.value() == 10
