import sys

import numpy as np
import PyQt6.QtCore as QtCore
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import sonaris.defaults as defaults
from sonaris.defaults import TICK_INTERVAL
from sonaris.frontend.managers.edux1002a import EDUX1002AManager
from sonaris.utils.log import get_logger

logger = get_logger()


class EDUX1002AOscilloscopeWidget(QWidget):
    def __init__(
        self,
        edux1002a_manager: EDUX1002AManager,
        parent=None,
        tick: int = TICK_INTERVAL,
    ):
        super().__init__(parent)
        self.edux1002a_manager = edux1002a_manager
        # self.edux1002a_manager.device.interface.debug = True
        self.tick = int(tick)
        self.active_channel = 1
        self.x_input = {1: None, 2: None}
        self.y_input = {1: None, 2: None}
        self.initUI()
        # Timer setup for real-time data update
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_data)
        self.configuration()
        self.timer.stop()

    def configuration(self):
        try:
            """configuration"""
            if self.edux1002a_manager.get_device():
                self.edux1002a_manager.device.set_acquisition_type("AVERage")
                self.edux1002a_manager.device.set_waveform_return_type("AVERage")
                self.edux1002a_manager.device.set_waveform_format("ASCII")
                self.edux1002a_manager.device.set_acquisition_complete(100)
                self.edux1002a_manager.device.set_acquisition_count(8)
                self.edux1002a_manager.device.set_waveform_points(
                    self.edux1002a_manager.buffer_size
                )
            else:
                logger.info(
                    "EDUX1002A not connnected, device configuration not started."
                )
        except Exception as e:
            logger.error(f"Error: {e}")

    def update_spinbox_values(self, xRange, yRange, x_input, y_input):
        x_input.blockSignals(True)
        y_input.blockSignals(True)

        x_input.setValue((xRange[0] + xRange[1]) / 2)
        y_input.setValue((yRange[0] + yRange[1]) / 2)

        x_input.blockSignals(False)
        y_input.blockSignals(False)

    def _create_channel_ui(self, channel: int):
        # Creating a group for better organization
        channel_group = QGroupBox(f"{channel}")
        channel_layout = QVBoxLayout()

        plot_widget = pg.PlotWidget()
        plot_widget.setBackground(defaults.GRAPH_RGB)

        plot_data = plot_widget.plot([], pen="y")
        channel_layout.addWidget(plot_widget)

        # Interactive axis controls
        axis_layout = QHBoxLayout()
        axis_layout.addWidget(QLabel("X-axis:"))

        self.x_input[channel] = QDoubleSpinBox()
        self.x_input[channel].setRange(-1e6, 1e6)
        self.x_input[channel].valueChanged.connect(
            lambda val: (
                plot_widget.setXRange(-val, val),
                self.x_input[channel].blockSignals(True),
                self.x_input[channel].setValue(val),
                self.x_input[channel].blockSignals(False),
            )
        )

        axis_layout.addWidget(self.x_input[channel])

        x_zoom_in = QPushButton("+")
        x_zoom_in.clicked.connect(
            lambda: (
                plot_widget.blockSignals(True),
                plot_widget.setXRange(
                    *[axis * 0.9 for axis in plot_widget.viewRange()[0]]
                ),
                plot_widget.blockSignals(False),
            )
        )

        axis_layout.addWidget(x_zoom_in)

        x_zoom_out = QPushButton("-")
        # For X-axis zoom out button:
        x_zoom_out.clicked.connect(
            lambda: (
                plot_widget.blockSignals(True),
                plot_widget.setXRange(
                    *[axis * 1.1 for axis in plot_widget.viewRange()[0]]
                ),
                plot_widget.blockSignals(False),
            )
        )
        axis_layout.addWidget(x_zoom_out)

        axis_layout.addWidget(QLabel("Y-axis:"))

        self.y_input[channel] = QDoubleSpinBox()
        self.y_input[channel].setRange(-1e6, 1e6)
        # For Y-axis spinbox:
        self.y_input[channel].valueChanged.connect(
            lambda val: (
                plot_widget.setYRange(-val, val),
                self.y_input[channel].blockSignals(True),
                self.y_input[channel].setValue(val),
                self.y_input[channel].blockSignals(False),
            )
        )

        y_zoom_in = QPushButton("+")
        y_zoom_in.clicked.connect(
            lambda: (
                plot_widget.blockSignals(True),
                plot_widget.setYRange(
                    *[axis * 0.9 for axis in plot_widget.viewRange()[1]]
                ),
                plot_widget.blockSignals(False),
            )
        )
        axis_layout.addWidget(y_zoom_in)

        y_zoom_out = QPushButton("-")
        y_zoom_out.clicked.connect(
            lambda: (
                plot_widget.blockSignals(True),
                plot_widget.setYRange(
                    *[axis * 1.1 for axis in plot_widget.viewRange()[1]]
                ),
                plot_widget.blockSignals(False),
            )
        )
        axis_layout.addWidget(y_zoom_out)

        channel_layout.addLayout(axis_layout)
        channel_group.setLayout(channel_layout)

        plot_widget.setFixedHeight(200)  # Fixed height, adjust as needed
        plot_widget.setBackground("k")  # Black background
        plot_widget.showGrid(x=True, y=True, alpha=0.5)  # Grid with semi-transparency

        # Color and style for the plot axes to make it more oscilloscope-like
        plot_widget.getAxis("left").setTextPen("w")
        plot_widget.getAxis("left").setPen("w")
        plot_widget.getAxis("bottom").setTextPen("w")
        plot_widget.getAxis("bottom").setPen("w")

        # Inside _create_channel_ui
        handler = self.make_range_changed_handler(
            self.x_input[channel], self.y_input[channel]
        )
        plot_widget.getViewBox().sigRangeChanged.connect(handler)

        # Inside _create_channel_ui, let's bind the channel buttons to the method to change channels
        channel_button = QPushButton(f"Channel {channel}")
        channel_button.clicked.connect(lambda: self.set_active_channel(channel))
        channel_layout.addWidget(channel_button)

        return channel_group, plot_data, channel_button

    def make_range_changed_handler(self, x_input, y_input):
        def handler(viewbox, ranges):
            xRange, yRange = ranges
            self.update_spinbox_values(xRange, yRange, x_input, y_input)

        return handler

    def initUI(self, **kwargs):
        layout = QHBoxLayout()
        self.plot_data = {1: None, 2: None}
        channel1_ui, self.plot_data[1], self.channel1_button = self._create_channel_ui(
            1
        )
        layout.addWidget(channel1_ui)

        channel2_ui, self.plot_data[2], self.channel2_button = self._create_channel_ui(
            2
        )
        layout.addWidget(channel2_ui)

        # Initialize channel button styles
        self.update_channel_button_styles()
        button_layout = QVBoxLayout()

        # Create the freeze/unfreeze button
        self.freeze_button = QPushButton("START")
        self.freeze_button.clicked.connect(self.toggle_freeze)
        button_layout.addWidget(self.freeze_button)

        self.auto_button = QPushButton("AUTO")
        self.auto_button.clicked.connect(
            lambda: self.edux1002a_manager.device.autoscale
        )
        button_layout.addWidget(self.auto_button)
        self.setLayout(layout)

        testbutton = QPushButton("Update")
        testbutton.clicked.connect(self.update_data)
        button_layout.addWidget(testbutton)
        layout.addLayout(button_layout)

    def update_channel_button_styles(self):
        if self.active_channel == 1:
            self.channel1_button.setStyleSheet("background-color: white")
            self.channel2_button.setStyleSheet("")
        else:
            self.channel2_button.setStyleSheet("background-color: white")
            self.channel1_button.setStyleSheet("")

    def set_active_channel(self, channel: int):
        try:
            self.active_channel = channel
            self.edux1002a_manager.get_device().setup_waveform_readout(channel)
            self.update_channel_button_styles()
        except Exception as e:
            logger.error(f"Error :{e}, is the device connected?")

    def update_data(self):
        try:
            self.edux1002a_manager.update_buffer(self.active_channel)
            voltage = self.edux1002a_manager.get_data(self.active_channel)
            time = np.arange(len(voltage))
            self.plot_data[self.active_channel].setData(time, voltage)
        except Exception as e:
            logger.error(f"Error: {e}, is the device connected?")
            self.freeze()

    def freeze(self):
        """Stop updating the waveform"""
        self.freeze_button.setText("START")
        self.freeze_button.setStyleSheet("")  # Set text color to default
        self.timer.stop()

    def unfreeze(self):
        """Resume updating the waveform"""
        self.timer.start(self.tick)
        self.freeze_button.setText("STOP")
        self.freeze_button.setStyleSheet("color: red;")

    def toggle_freeze(self):
        if self.timer.isActive():
            self.freeze()
        else:
            self.unfreeze()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    import pyvisa

    # Here you'd initialize your Interface and EDUX1002A class instances.
    rm = pyvisa.ResourceManager()
    oscilloscope = DeviceDetector(rm).detect_device()
    main_window = EDUX1002AOscilloscopeWidget(oscilloscope)
    main_window.show()

    sys.exit(app.exec())
