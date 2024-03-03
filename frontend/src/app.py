import argparse
import os
import signal
from pathlib import Path
from typing import Dict

import pyvisa
import qdarktheme
from frontend.header import OSCILLOSCOPE_BUFFER_SIZE, DeviceName
from frontend.managers.dg4202 import DG4202Manager
from frontend.managers.edux1002a import EDUX1002AManager
from frontend.managers.state_manager import StateManager
from frontend.pages import factory, general, monitor, scheduler, settings
from frontend.pages.general import GeneralPage
from frontend.pages.monitor import MonitorPage
from frontend.pages.scheduler import SchedulerPage
from frontend.pages.settings import SettingsPage
from frontend.tasks.tasks import get_tasks
from frontend.widgets.menu import MainMenuBar
from frontend.widgets.sidebar import Sidebar
from frontend.widgets.templates import ModularMainWindow
from PyQt6.QtCore import QLocale
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtWidgets import QApplication, QStackedWidget, QWidget

from scheduler.timekeeper import Timekeeper
from scheduler.worker import Worker

# Before creating your application instance
QLocale.setDefault(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))


def signal_handler(signum, frame):
    print("Exit signal detected.")
    # Invoke the default SIGINT handler to exit the application
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)


def init_objects(args_dict: dict):
    factory.resource_manager = pyvisa.ResourceManager()
    factory.state_manager = StateManager()
    factory.edux1002a_manager = EDUX1002AManager(
        state_manager=factory.state_manager,
        args_dict=args_dict,
        resource_manager=factory.resource_manager,
        buffer_size=OSCILLOSCOPE_BUFFER_SIZE,
    )
    factory.dg4202_manager = DG4202Manager(
        factory.state_manager,
        args_dict=args_dict,
        resource_manager=factory.resource_manager,
    )
    factory.worker = Worker(
        function_map_file=factory.FUNCTION_MAP_FILE,
        logfile=factory.WORKER_LOGS,
    )
    factory.timekeeper = Timekeeper(
        persistence_file=factory.TIMEKEEPER_JOBS_FILE,
        worker_instance=factory.worker,
        logfile=factory.TIMEKEEPER_LOGS,
    )

    for task_name, func_pointer in get_tasks(flatten=True).items():
        factory.worker.register_task(func_pointer, task_name)

    factory.worker.start_worker()


class MainWindow(ModularMainWindow):
    def __init__(self, args_dict: dict) -> None:
        super().__init__()
        menu_bar = MainMenuBar(self)
        self.setWindowTitle("MRI Labs")
        self.setMenuBar(menu_bar)
        self.last_page = ""
        # ---------------------------------------------------------------------- #
        # ---------------------------SIDEBAR SETUP------------------------------ #
        self.sidebar = Sidebar(self)
        device_managers = {
            DeviceName.DG4202.value: factory.dg4202_manager,
            DeviceName.EDUX1002A.value: factory.edux1002a_manager,
        }
        self.sidebar.sizePolicy()
        self.sidebar_dict: Dict[str, QWidget] = {
            GeneralPage.PAGE_NAME: GeneralPage(
                dg4202_manager=factory.dg4202_manager,
                edux1002a_manager=factory.edux1002a_manager,
                parent=self,
                args_dict=args_dict,
                root_callback=self.root_callback,
            ),
            SchedulerPage.PAGE_NAME: SchedulerPage(
                timekeeper=factory.timekeeper,
                parent=self,
                args_dict=args_dict,
                root_callback=self.root_callback,
            ),
            MonitorPage.PAGE_NAME: MonitorPage(
                device_managers=device_managers,
                parent=self,
                args_dict=args_dict,
                monitor_logs=factory.MONITOR_FILE,
                root_callback=self.root_callback,
            ),
            SettingsPage.PAGE_NAME: SettingsPage(
                device_managers=device_managers,
                parent=self,
                args_dict=args_dict,
                root_callback=self.root_callback,
            ),
        }
        self.sidebar.addItems(self.sidebar_dict.keys())  # Add strings to sidebar items
        self.sidebar_content = QStackedWidget(self)
        list(
            map(self.sidebar_content.addWidget, self.sidebar_dict.values())
        )  # Adds all child widgets to content widgets

        # --------------------------------------------------------------------- #
        # ---------------------------LAYOUT SETUP------------------------------ #
        # --------------------------------------------------------------------- #

        self.add_widget_to_left(self.sidebar)
        self.add_widget_to_middle(
            self.sidebar_content
        )  # Use the method from ModularMainWindow
        # Connect the Sidebar's custom signal to the MainWindow's slot
        self.sidebar.pageSelected.connect(self.loadPage)

    def loadPage(self, page_name: str) -> None:
        page_widget: QWidget = self.sidebar_dict.get(page_name)
        if page_widget and self.last_page != page_name:
            self.sidebar_content.setCurrentWidget(page_widget)
            print(f"[Sidebar] Switch event to {page_name}")
            page_widget.update()
            self.last_page = page_name

    def root_callback(self):
        """tells pages the pages to call update method."""
        for _, page_obj in self.sidebar_dict.items():
            page_obj.update()

    def closeEvent(self, event):
        print("main x exit button was clicked")
        factory.worker.stop_worker()
        super().closeEvent(event)

    def showEvent(self, event):
        primaryScreen = QGuiApplication.primaryScreen()
        screenGeometry = primaryScreen.availableGeometry()
        centerPoint = screenGeometry.center()
        frameGeometry = self.frameGeometry()
        frameGeometry.moveCenter(centerPoint)
        self.move(frameGeometry.topLeft())
        super().showEvent(event)


def create_app(args_dict: dict) -> (QApplication, MainWindow):
    init_objects(args_dict=args_dict)

    app = QApplication([])
    window = MainWindow(args_dict)

    qdarktheme.setup_theme()

    app_icon = QIcon(Path(os.getenv("ASSETS"), "favicon.ico").as_posix())
    app.setWindowIcon(app_icon)
    window.setWindowIcon(app_icon)

    window.setWindowTitle("mrilabs")
    window.resize(640, 400)
    print("Window size after resize:", window.size())
    return app, window


def run_application():
    parser = argparse.ArgumentParser(description="Run the mrilabs application.")
    parser.add_argument(
        "--hardware-mock",
        action="store_true",
        help="Run the app in hardware mock mode.",
    )

    args = parser.parse_args()
    args_dict = vars(args)
    print(args_dict)
    app, window = create_app(args_dict)
    window.show()
    app.exec()


if __name__ == "__main__":
    run_application()
