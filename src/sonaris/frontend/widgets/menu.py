from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QFileDialog, QMenu, QMenuBar, QMessageBox

from sonaris.frontend.widgets.windows import DeviceWindow, VersionWindow


class MainMenuBar(QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        # File Menu
        fileMenu = QMenu("&File", self)
        self.version_window = VersionWindow(self.parent())
        self.device_window = DeviceWindow()
        self.addMenu(fileMenu)

        # Save State Action
        saveAct = QAction("&Save State", self)
        saveAct.setShortcut(QKeySequence("Ctrl+S"))
        saveAct.setStatusTip("Saves the program state")
        saveAct.triggered.connect(self.save_state)  # Assuming save_state method exists
        fileMenu.addAction(saveAct)

        # Open State Action
        openAct = QAction("&Open State...", self)
        openAct.setShortcut(QKeySequence("Ctrl+O"))
        openAct.setStatusTip("Opens a saved program state")
        openAct.triggered.connect(self.open_state)
        fileMenu.addAction(openAct)

        # Exit Action
        exitAct = QAction("E&xit", self)
        exitAct.setShortcut(QKeySequence("Alt+F4"))
        exitAct.setStatusTip("Exits the application")
        exitAct.triggered.connect(self.exit_app)  # Assuming exit_app method exists
        fileMenu.addAction(exitAct)
        # Device Menu
        deviceMenu = QMenu("&Device", self)
        self.addMenu(deviceMenu)

        # Device Window Action
        deviceAct = QAction("&Device Window", self)
        deviceAct.setShortcut(QKeySequence("Ctrl+D"))
        deviceAct.setStatusTip("Displays device window")
        deviceAct.triggered.connect(
            self.show_device_window
        )  # Assuming show_device_window method exists
        deviceMenu.addAction(deviceAct)

        # Help Menu
        helpMenu = QMenu("&Help", self)
        self.addMenu(helpMenu)

        # Version Action
        versionAct = QAction("&Version", self)
        versionAct.setStatusTip("Displays version window and developer notes")
        versionAct.triggered.connect(
            self.show_version
        )  # Assuming show_version method exists
        helpMenu.addAction(versionAct)

    def save_state(self):
        # Opens a dialog to save a file
        fileName, _ = QFileDialog.getSaveFileName(
            self, "Save State", "", "State Files (*.state)"
        )
        if fileName:
            self.perform_save(
                fileName
            )  # Assuming perform_save method exists to actually save the state

    def open_state(self):
        # Opens a dialog to open a file
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Open State", "", "State Files (*.state)"
        )
        if fileName:
            self.perform_open(fileName)

    def perform_save(self, fileName):
        # Implement the actual save functionality here
        pass

    def perform_open(self, fileName):
        # Implement the actual open functionality here
        pass

    def exit_app(self):
        # Exit the application
        reply = QMessageBox.warning(
            self,
            "Exit",
            "Application will be closed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.parent().close()  # Or QApplication.instance().quit()

    def show_version(self):
        # Opens the version info window
        self.version_window.show()

    def show_device_window(self):
        self.device_window.show()
