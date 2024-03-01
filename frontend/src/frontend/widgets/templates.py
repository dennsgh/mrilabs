from abc import ABC, abstractmethod
from typing import Callable

from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)


class BasePage(QWidget):
    def __init__(
        self,
        parent=None,
        args_dict: dict = None,
        root_callback: Callable = None,
    ):
        super().__init__(parent)
        self.args_dict: dict = args_dict
        self.root_callback: Callable = root_callback

    @abstractmethod
    def update(self):
        pass


class ModuleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    @abstractmethod
    def initUI(self, **kwargs):
        """Implement this method to define the layout for the widget"""
        raise NotImplementedError


class CollapsibleWidget(ModuleWidget):
    def __init__(
        self, content_widget: QWidget, orientation: str = "horizontal", parent=None
    ):
        super().__init__(parent)
        self.content_widget = content_widget
        self.orientation = orientation
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout(self)
        self.toggle_button = QPushButton("Collapse", self)
        self.toggle_button.clicked.connect(self.toggleContent)
        self.main_layout.addWidget(self.toggle_button)
        self.main_layout.addWidget(self.content_widget)
        self.setLayout(self.main_layout)

    def toggleContent(self):
        if self.content_widget.isVisible():
            self.content_widget.hide()
        else:
            self.content_widget.show()


class ModularMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create the central grid layout
        self.grid_layout = QGridLayout()

        # Directional layouts
        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()
        self.top_layout = QHBoxLayout()
        self.bottom_layout = QHBoxLayout()
        self.middle_layout = QStackedLayout()

        # Add the directional layouts to the grid layout
        self.grid_layout.addLayout(self.top_layout, 0, 1)
        self.grid_layout.addLayout(self.left_layout, 1, 0)
        self.grid_layout.addLayout(self.right_layout, 1, 2)
        self.grid_layout.addLayout(self.bottom_layout, 2, 1)

        self.grid_layout.addLayout(self.middle_layout, 1, 1)

        # Setup central widget
        central_widget = QWidget()
        central_widget.setLayout(self.grid_layout)
        self.setCentralWidget(central_widget)

    def add_widget_to_left(self, widget: QWidget):
        self.left_layout.addWidget(widget)

    def add_widget_to_right(self, widget: QWidget):
        self.right_layout.addWidget(widget)

    def add_widget_to_middle(self, widget: QWidget):
        self.middle_layout.addWidget(widget)

    def add_widget_to_top(self, widget: QWidget):
        self.top_layout.addWidget(widget)

    def add_widget_to_bottom(self, widget: QWidget):
        self.bottom_layout.addWidget(widget)
