import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import pyvisa
from features.managers import DG4202Manager, EDUX1002AManager, StateManager
from features.tasks import get_tasks
from pages import experiment, factory, general, settings
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget
from qt_material import apply_stylesheet
from widgets.menu import MainMenuBar
from widgets.sidebar import Sidebar
from widgets.templates import ModularMainWindow

from scheduler.timekeeper import Timekeeper
from scheduler.worker import Worker

OSCILLOSCOPE_BUFFER_SIZE = 512


def signal_handler(signal, frame):
    print("Exit signal detected.")
    # Perform additional error handling actions here if needed
    sys.exit(0)


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
        function_map_file=Path(os.getenv("DATA"), "registered_tasks.json"),
        logfile=Path(os.getenv("LOGS"), "worker.log"),
    )
    factory.timekeeper = Timekeeper(
        persistence_file=Path(os.getenv("DATA"), "jobs.json"),
        worker_instance=factory.worker,
        logfile=Path(os.getenv("LOGS"), "timekeeper.log"),
    )

    factory.state_manager.write_state({"dg_last_alive": None})

    for task_name, func_pointer in get_tasks():
        factory.worker.register_task(func_pointer, task_name)


class MainWindow(ModularMainWindow):
    def __init__(self, args_dict: dict) -> None:
        super().__init__()
        menu_bar = MainMenuBar(self)
        self.setWindowTitle("MRI Labs")
        self.setMenuBar(menu_bar)
        # ---------------------------------------------------------------------- #
        # ---------------------------SIDEBAR SETUP------------------------------ #
        self.sidebar = Sidebar(self)

        self.sidebar.sizePolicy()
        self.sidebar_dict: Dict[str, QWidget] = {
            "General": general.GeneralPage(
                factory.dg4202_manager,
                factory.edux1002a_manager,
                self,
                args_dict=args_dict,
            ),
            "Experiment": experiment.ExperimentPage(
                factory.dg4202_manager, self, args_dict
            ),
            "Settings": settings.SettingsPage(self, args_dict),
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
        page_widget: Optional[QWidget] = self.sidebar_dict.get(page_name)
        if page_widget:
            self.sidebar_content.setCurrentWidget(page_widget)


def create_app(args_dict: dict) -> (QApplication, QMainWindow):
    init_objects(args_dict=args_dict)

    app = QApplication([])
    window = MainWindow(args_dict)
    apply_stylesheet(app, theme="dark_blue.xml")
    window.setWindowTitle("mrilabs")
    window.show()
    return app, window


def run_application():
    parser = argparse.ArgumentParser(description="Run the mrilabs application.")
    parser.add_argument(
        "--hardware-mock",
        action="store_true",
        help="Run the app in hardware mock mode.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Run the application in debug mode.",
    )
    parser.add_argument(
        "--api-server", type=int, help="Launch an api server on the specified port."
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8501,
        help="Specify the port number to run on. Defaults to 8501.",
    )
    parser.add_argument(
        "--env",
        type=str,
        default="development",
        choices=["development", "production"],
        help="Specify the environment to run the application in. Defaults to development.",
    )

    args = parser.parse_args()
    args_dict = vars(args)
    print(args_dict)
    app, window = create_app(args_dict)
    app.exec()


if __name__ == "__main__":
    run_application()
