from typing import Callable

from pages import factory
from PyQt6.QtWidgets import QVBoxLayout
from widgets.job_scheduler import SchedulerWidget

from scheduler.timekeeper import Timekeeper
from widgets.templates import BasePage

class SchedulerPage(BasePage):
    def __init__(
        self,
        timekeeper: Timekeeper = None,
        parent=None,
        args_dict: dict = None,
        root_callback: Callable = None,
    ):
        super().__init__(
            parent=parent, args_dict=args_dict, root_callback=root_callback
        )
        self.args_dict = args_dict
        self.timekeeper = timekeeper or factory.timekeeper
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout()
        self.scheduler_widget = SchedulerWidget(self.timekeeper, self.root_callback)
        # Adding the tab widget to the main layout
        self.main_layout.addWidget(self.scheduler_widget)

        self.setLayout(self.main_layout)

    def update(self):
        pass
