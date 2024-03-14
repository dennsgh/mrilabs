from datetime import datetime

import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from sonaris.device.dg4202 import DG4202
from sonaris.defaults import DECIMAL_POINTS, NOT_FOUND_STRING
from sonaris.frontend.managers.dg4202 import DG4202Manager
from sonaris.frontend.pages import plotter
from sonaris.utils.log import get_logger

logger = get_logger()


class DG4202SignalGeneratorWidget(QWidget):
    def __init__(self, dg4202_manager: DG4202Manager, parent=None):
        super().__init__(parent=parent)
        self.sweep_plot_data = {1: None, 2: None}
        self.waveform_plot_data = {1: None, 2: None}
        self.channel_count = 2
        self.link_channel = False
        self.dg4202_manager = dg4202_manager
        self.all_parameters = self.dg4202_manager.get_data()
        self.input_objects = {1: {}, 2: {}}
        self.initUI()

    def check_connection(self) -> bool:
        self.dg4202_manager.device = self.dg4202_manager.get_device()
        self.all_parameters = self.dg4202_manager.get_data()

        if self.dg4202_manager.device is None:
            return False

        is_alive = self.dg4202_manager.device.is_connection_alive()
        if not is_alive:
            self.dg4202_manager.device = None
        return is_alive

    def create_widgets(self):
        # A dictionary to store widgets for each channel by channel number
        self.controls = {}

        for channel in range(1, self.channel_count + 1):
            # Main controls widget
            main_controls_widget = self.generate_main_controls(channel)

            # Individual control widgets
            waveform_control = self.generate_waveform_control(channel)
            sweep_control = self.generate_sweep_control(channel)

            # Store widgets in dictionary
            self.controls[channel] = {
                "main_controls": main_controls_widget,
                "waveform_control": waveform_control,
                "sweep_control": sweep_control,
            }

    def initUI(self):
        self.create_widgets()
        self.main_layout = QVBoxLayout()
        self.check_connection()
        self.status_label = QLabel("")
        self.main_layout.addWidget(self.status_label)
        for _, widgets in self.controls.items():
            # Add main controls for the channel

            tab_widget = QTabWidget()
            tab_widget.addTab(widgets["waveform_control"], "Default")
            tab_widget.addTab(widgets["sweep_control"], "Sweep")
            tab_widget.setMaximumHeight(250)
            self.main_layout.addWidget(tab_widget)
            tab_widget.currentChanged.connect(self.on_tab_changed)
            self.main_layout.addWidget(widgets["main_controls"])

        self.main_layout.setSpacing(5)  # Reduced spacing
        self.main_layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins

        self.setLayout(self.main_layout)

    def generate_main_controls(self, channel: int) -> QWidget:

        # Setting up main layout
        main_layout = QVBoxLayout()

        control_layout = QHBoxLayout()
        # Adding tabs for modes
        # Add more tabs as needed
        self.input_objects[channel]["TOGGLE_OUTPUT"] = QPushButton(
            f"Output CH{channel}"
        )
        self.input_objects[channel]["TOGGLE_OUTPUT"].clicked.connect(
            lambda: self.toggle_output(channel)
        )
        self.update_button_state(channel)
        control_layout.addWidget(self.input_objects[channel]["TOGGLE_OUTPUT"])

        main_layout.addLayout(control_layout)

        # Create a QWidget to return
        main_controls_widget = QWidget()
        main_controls_widget.setLayout(main_layout)
        return main_controls_widget

    def generate_sweep_control(self, channel: int) -> QWidget:
        """
        Generate the control components for the sweep mode.

        Parameters:
            channel (int): The channel number.

        Returns:
            QWidget: The widget containing the sweep control components.
        """

        # ---- LEFT COLUMN ---- #
        left_first_column_layout = QFormLayout()
        left_second_column_layout = QFormLayout()

        # Sweep input
        duration_input = QLineEdit(self)
        duration_input.setPlaceholderText(f"Sweep duration frequency CH{channel}")
        self.input_objects[channel]["TIME"] = duration_input
        # Set the text of the sweep input to the current value
        current_sweep_value = str(
            self.all_parameters.get(f"{channel}", {})
            .get("mode", {})
            .get("parameters", {})
            .get("sweep", {})
            .get("TIME", 0.0)
        )
        duration_input.setText(current_sweep_value)
        left_first_column_layout.addRow("Sweep (s):", duration_input)

        # Return time input
        rtime_input = QLineEdit(self)
        rtime_input.setPlaceholderText(f"Sweep return time CH{channel}")
        self.input_objects[channel]["RTIME"] = rtime_input
        # Set the text of the return time input to the current value
        current_rtime_value = str(
            self.all_parameters.get(f"{channel}", {})
            .get("mode", {})
            .get("parameters", {})
            .get("sweep", {})
            .get("RTIME", 0.0)
        )
        rtime_input.setText(current_rtime_value)
        left_first_column_layout.addRow("Return (ms):", rtime_input)

        # Start frequency input
        fstart_input = QLineEdit(self)
        fstart_input.setPlaceholderText(f"Sweep start frequency CH{channel}")
        self.input_objects[channel]["FSTART"] = fstart_input
        # Set the text of the start frequency input to the current value
        current_fstart_value = str(
            self.all_parameters.get(f"{channel}", {})
            .get("mode", {})
            .get("parameters", {})
            .get("sweep", {})
            .get("FSTART", 0.0)
        )
        fstart_input.setText(current_fstart_value)
        left_first_column_layout.addRow("Start (Hz):", fstart_input)

        # Stop frequency input
        fstop_input = QLineEdit(self)
        fstop_input.setPlaceholderText(f"Sweep stop frequency CH{channel}")
        self.input_objects[channel]["FSTOP"] = fstop_input
        # Set the text of the stop frequency input to the current value
        current_fstop_value = str(
            self.all_parameters.get(f"{channel}", {})
            .get("mode", {})
            .get("parameters", {})
            .get("sweep", {})
            .get("FSTOP", 0.0)
        )
        fstop_input.setText(current_fstop_value)
        left_second_column_layout.addRow("Stop (Hz):", fstop_input)

        # Hold Start input
        htime_start_input = QLineEdit(self)
        htime_start_input.setPlaceholderText(f"Start hold time CH{channel}")
        self.input_objects[channel]["HTIME_START"] = htime_start_input
        # Set the text of the start hold time input to the current value
        current_htime_start_value = str(
            self.all_parameters.get(f"{channel}", {})
            .get("mode", {})
            .get("parameters", {})
            .get("sweep", {})
            .get("HTIME_START", 0.0)
        )
        htime_start_input.setText(current_htime_start_value)
        left_second_column_layout.addRow("Start Hold (ms):", htime_start_input)

        # Hold Stop input
        htime_stop_input = QLineEdit(self)
        htime_stop_input.setPlaceholderText(f"Stop hold time CH{channel}")
        self.input_objects[channel]["HTIME_STOP"] = htime_stop_input
        # Set the text of the stop hold time input to the current value
        current_htime_stop_value = str(
            self.all_parameters.get(f"{channel}", {})
            .get("mode", {})
            .get("parameters", {})
            .get("sweep", {})
            .get("HTIME_STOP", 0.0)
        )
        htime_stop_input.setText(current_htime_stop_value)
        left_second_column_layout.addRow("Stop Hold (ms):", htime_stop_input)

        # Set parameters button
        set_parameters_button = QPushButton(f"Set Parameters CH{channel}", self)
        set_parameters_button.clicked.connect(
            lambda: self.on_update_sweep(
                channel,
                duration_input.text(),
                rtime_input.text(),
                fstart_input.text(),
                fstop_input.text(),
                htime_start_input.text(),
                htime_stop_input.text(),
            )
        )
        left_columns_layout = QHBoxLayout()
        left_columns_layout.addLayout(left_first_column_layout)
        left_columns_layout.addLayout(left_second_column_layout)

        # Create a vertical layout to hold the columns and the button
        left_main_layout = QVBoxLayout()
        left_main_layout.addLayout(left_columns_layout)  # Add the columns layout

        # Set parameters button
        left_main_layout.addWidget(
            set_parameters_button
        )  # Adding the button below the columns

        # Wrap the main left layout in a widget
        left_widget = QWidget()
        left_widget.setLayout(left_main_layout)

        # ---- RIGHT COLUMN (Sweep Plot) ---- #
        right_column_layout = QVBoxLayout()
        plot_widget = pg.PlotWidget()
        plot_widget.setLabel("left", "Amplitude", units="V")
        plot_widget.setLabel("bottom", "Time", units="s")
        self.sweep_plot_data[channel] = plot_widget.plot([], pen="y")
        right_column_layout.addWidget(
            plot_widget, alignment=Qt.AlignmentFlag.AlignCenter
        )

        right_widget = QWidget()
        right_widget.setLayout(right_column_layout)

        # ---- COMBINE AND RETURN ---- #
        layout = QHBoxLayout()
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)

        widget = QWidget()
        widget.setLayout(layout)
        self.update_sweep_graph(channel)
        return widget

    def generate_waveform_control(self, channel: int) -> QWidget:
        """
        Generate the control components for the waveform mode.

        Parameters:
            channel (int): The channel number.

        Returns:
            QWidget: The widget containing the waveform control components.
        """

        # Create main container and layout
        channel_widget = QWidget()
        channel_layout = QHBoxLayout()

        # ---- LEFT COLUMN ---- #
        left_column_layout = QFormLayout()

        # Waveform type dropdown
        waveform_type = QComboBox()
        waveform_type.addItems(DG4202.available_waveforms())
        self.input_objects[channel]["WAVEFORM_TYPE"] = waveform_type
        left_column_layout.addRow(f"Waveform Type CH{channel}", waveform_type)

        # Frequency input with QDoubleSpinBox
        freq_input = QDoubleSpinBox()
        freq_input.setDecimals(DECIMAL_POINTS)
        freq_input.setMaximum(self.dg4202_manager.device_type.FREQ_LIMIT)
        freq_input.setValue(
            self.all_parameters.get(f"{channel}", {})
            .get("waveform", {})
            .get("frequency", 0.0)
        )
        self.input_objects[channel]["FREQUENCY"] = freq_input
        left_column_layout.addRow("Frequency (Hz)", freq_input)

        # Amplitude input with QDoubleSpinBox
        amp_input = QDoubleSpinBox()
        amp_input.setDecimals(DECIMAL_POINTS)
        amp_input.setMaximum(5.0)  # 5V limit
        amp_input.setValue(
            self.all_parameters.get(f"{channel}", {})
            .get("waveform", {})
            .get("amplitude", 0.0)
        )
        self.input_objects[channel]["AMPLITUDE"] = amp_input
        left_column_layout.addRow("Amplitude (V)", amp_input)

        # Offset input with QDoubleSpinBox
        offset_input = QDoubleSpinBox()
        offset_input.setDecimals(DECIMAL_POINTS)
        offset_input.setMaximum(5.0)  # 5V limit
        offset_input.setValue(
            self.all_parameters.get(f"{channel}", {})
            .get("waveform", {})
            .get("offset", 0.0)
        )
        self.input_objects[channel]["OFFSET"] = offset_input
        left_column_layout.addRow("Offset (V)", offset_input)

        # Set waveform button
        set_waveform_button = QPushButton(f"Set Waveform CH{channel}")
        set_waveform_button.clicked.connect(
            lambda: self.on_update_waveform(
                channel,
                waveform_type.currentText(),
                float(freq_input.text()),
                float(amp_input.text()),
                float(offset_input.text()),
            )
        )
        left_column_layout.addRow(set_waveform_button)

        # Add to main layout
        left_widget = QWidget()
        left_widget.setLayout(left_column_layout)
        channel_layout.addWidget(left_widget)

        # ---- RIGHT COLUMN (Waveform Plot) ---- #
        right_column_layout = QVBoxLayout()
        plot_widget = pg.PlotWidget()
        plot_widget.setLabel("left", "Amplitude", units="V")
        plot_widget.setLabel("bottom", "Time", units="s")
        self.waveform_plot_data[channel] = plot_widget.plot([], pen="y")
        # Add spacers to constrain the size of the plot widget
        right_column_layout.addSpacerItem(
            QSpacerItem(
                20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )
        right_column_layout.addWidget(
            plot_widget, alignment=Qt.AlignmentFlag.AlignCenter
        )
        right_column_layout.addSpacerItem(
            QSpacerItem(
                20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            )
        )
        # Add to main layout
        right_widget = QWidget()
        right_widget.setLayout(right_column_layout)
        channel_layout.addWidget(right_widget, 0)

        # ---- COMBINE AND RETURN ---- #
        channel_widget.setLayout(channel_layout)
        self.update_waveform_graph(channel)
        return channel_widget

    def on_update_sweep(
        self,
        channel: int,
        sweep: float,
        rtime: float,
        fstart: float,
        fstop: float,
        htime_start: float,
        htime_stop: float,
    ):
        try:
            if self.dg4202_manager.get_device():
                sweep = (
                    float(sweep)
                    if sweep
                    else float(
                        self.all_parameters.get(f"{channel}", {})
                        .get("mode", {})
                        .get("parameters", {})
                        .get("sweep", {})
                        .get("TIME", 0.0)
                    )
                )
                rtime = (
                    float(rtime)
                    if rtime
                    else float(
                        self.all_parameters.get(f"{channel}", {})
                        .get("mode", {})
                        .get("parameters", {})
                        .get("sweep", {})
                        .get("RTIME", 0.0)
                    )
                )
                fstart = (
                    float(fstart)
                    if fstart
                    else float(
                        self.all_parameters.get(f"{channel}", {})
                        .get("mode", {})
                        .get("parameters", {})
                        .get("sweep", {})
                        .get("FSTART", 0.0)
                    )
                )
                fstop = (
                    float(fstop)
                    if fstop
                    else float(
                        self.all_parameters.get(f"{channel}", {})
                        .get("mode", {})
                        .get("parameters", {})
                        .get("sweep", {})
                        .get("FSTOP", 0.0)
                    )
                )
                htime_start = (
                    float(htime_start)
                    if htime_start
                    else float(
                        self.all_parameters.get(f"{channel}", {})
                        .get("mode", {})
                        .get("parameters", {})
                        .get("sweep", {})
                        .get("HTIME_START", 0.0)
                    )
                )
                htime_stop = (
                    float(htime_stop)
                    if htime_stop
                    else float(
                        self.all_parameters.get(f"{channel}", {})
                        .get("mode", {})
                        .get("parameters", {})
                        .get("sweep", {})
                        .get("HTIME_STOP", 0.0)
                    )
                )
                params = {
                    "TIME": sweep,
                    "RTIME": rtime,
                    "FSTART": fstart,
                    "FSTOP": fstop,
                    "HTIME_START": htime_start,
                    "HTIME_STOP": htime_stop,
                }
                logger.info(params)
                self.dg4202_manager.device.set_sweep_parameters(channel, params)
                self.update_sweep_graph(channel)
            else:
                logger.error(f"{NOT_FOUND_STRING} Is device connected?.")
        except Exception as e:
            logger.error(f"Error:{e}")

    def toggle_output(self, channel: int):
        """
        Toggle the output for the given channel.

        Parameters:
            channel (int): The channel number.
        """
        try:
            if self.check_connection():
                set_to = (
                    False
                    if self.all_parameters.get(f"{channel}", {}).get(
                        "output_status", "ERR"
                    )
                    == "ON"
                    else True
                )
                logger.info(
                    f'{channel} is {self.all_parameters.get(f"{channel}", {}).get("output_status", "ERR")} -> {set_to}'
                )
                self.dg4202_manager.device.output_on_off(channel, set_to)
                self.check_connection()  # updates dictionary
                # Update the button state after toggling the output

            else:
                logger.error(f"{NOT_FOUND_STRING} Is device connected?")
            self.update_button_state(channel)
        except Exception as e:
            logger.error(f"Error:{e}")

    def update_button_state(self, channel: int):
        """
        Update the button's appearance and text based on the output status.

        Parameters:
            output_btn (QPushButton): The output button to be updated.
            channel (int): The channel number.
        """
        status = self.all_parameters.get(f"{channel}", {}).get("output_status", "ERR")
        if status == "ON":
            self.input_objects[channel]["TOGGLE_OUTPUT"].setStyleSheet(
                "background-color: white; color: black;"
            )
            self.input_objects[channel]["TOGGLE_OUTPUT"].setText(
                f"Output CH{channel} ON"
            )
        else:
            self.input_objects[channel]["TOGGLE_OUTPUT"].setStyleSheet(
                "background-color: none; color: white;"
            )
            self.input_objects[channel]["TOGGLE_OUTPUT"].setText(
                f"Output CH{channel} OFF"
            )

    def on_tab_changed(self, index):
        # Placeholder for an API call. Replace with actual logic later.
        if index == 0:  # Assuming 0 is the index for the "Sweep" tab
            pass  # API call for "Sweep"
        elif index == 1:  # Assuming 1 is the index for the "Waveform" tab
            pass  # API call for "Waveform"
        # Add more conditions for other tabs

        # Connect the signal

    def on_update_waveform(
        self,
        channel: int,
        waveform_type: str,
        frequency: float,
        amplitude: float,
        offset: float,
    ):
        """
        Update the waveform parameters and plot.

        Parameters:
            channel (int): The channel number.
            waveform_type (str): The selected waveform type.
            frequency (float): The selected frequency.
            amplitude (float): The selected amplitude.
            offset (float): The selected offset.
            self.waveform_plot_data (float): Plot data reference.
        """
        try:
            if self.dg4202_manager.get_device():
                frequency = frequency or float(
                    self.all_parameters[f"{channel}"]["waveform"]["frequency"]
                )
                amplitude = amplitude or float(
                    self.all_parameters[f"{channel}"]["waveform"]["amplitude"]
                )
                offset = offset or float(
                    self.all_parameters[f"{channel}"]["waveform"]["offset"]
                )
                waveform_type = (
                    waveform_type
                    or self.all_parameters[f"{channel}"]["waveform"]["waveform_type"]
                )

                # If a parameter is not set, pass the current value
                self.dg4202_manager.device.set_waveform(
                    channel, waveform_type, frequency, amplitude, offset
                )

                if self.link_channel:
                    self.dg4202_manager.device.set_waveform(
                        2 if channel == 1 else 1,
                        waveform_type,
                        frequency,
                        amplitude,
                        offset,
                    )

                # Update some status label or log if you have one
                status_string = f"[{datetime.now().isoformat()}] Waveform updated."
                # Assuming you have a status_label in your UI
                self.status_label.setText(status_string)
                self.update_waveform_graph(channel)
                logger.info(
                    f"Waveform updated [CH:{channel}] {waveform_type} FREQ:{frequency} AMP:{amplitude} OFF{offset}"
                )
            else:
                self.status_label.setText(NOT_FOUND_STRING)
                logger.error(f"{NOT_FOUND_STRING} Is device connected?")

        except Exception as e:
            logger.error("Error: %s, ", e)

    def update_waveform_graph(self, channel):
        self.check_connection()
        x_data, y_data = plotter.plot_waveform(
            params=self.all_parameters[f"{channel}"]["waveform"]
        )
        self.waveform_plot_data[channel].setData(x_data, y_data)

    def update_sweep_graph(self, channel):
        self.check_connection()
        x_data, y_data = plotter.plot_sweep(
            start_frequency=self.all_parameters[f"{channel}"]["mode"]["parameters"][
                "sweep"
            ]["FSTART"],
            stop_frequency=self.all_parameters[f"{channel}"]["mode"]["parameters"][
                "sweep"
            ]["FSTOP"],
            duration=self.all_parameters[f"{channel}"]["mode"]["parameters"]["sweep"][
                "TIME"
            ],
            rtime=self.all_parameters[f"{channel}"]["mode"]["parameters"]["sweep"][
                "RTIME"
            ],
            htime_start=self.all_parameters[f"{channel}"]["mode"]["parameters"][
                "sweep"
            ]["HTIME_START"],
            htime_stop=self.all_parameters[f"{channel}"]["mode"]["parameters"]["sweep"][
                "HTIME_STOP"
            ],
        )
        self.sweep_plot_data[channel].setData(x_data, y_data)

    def update(self):
        if self.check_connection():
            for channel in range(1, self.channel_count + 1):
                self.update_waveform_graph(channel)
                self.update_sweep_graph(channel)
                self.update_button_state(channel)
                self.update_input_fields(channel)

    def update_input_fields(self, channel: int):
        sweep_parameters = self.all_parameters[f"{channel}"]["mode"]["parameters"][
            "sweep"
        ]
        waveform_parameters = self.all_parameters[f"{channel}"]["waveform"]

        # Update sweep parameters
        self.input_objects[channel]["TIME"].setText(str(sweep_parameters["TIME"]))
        self.input_objects[channel]["RTIME"].setText(str(sweep_parameters["RTIME"]))
        self.input_objects[channel]["FSTART"].setText(str(sweep_parameters["FSTART"]))
        self.input_objects[channel]["FSTOP"].setText(str(sweep_parameters["FSTOP"]))
        self.input_objects[channel]["HTIME_START"].setText(
            str(sweep_parameters["HTIME_START"])
        )
        self.input_objects[channel]["HTIME_STOP"].setText(
            str(sweep_parameters["HTIME_STOP"])
        )

        # Update waveform parameters
        self.input_objects[channel]["FREQUENCY"].setValue(
            waveform_parameters["frequency"]
        )
        self.input_objects[channel]["AMPLITUDE"].setValue(
            waveform_parameters["amplitude"]
        )
        self.input_objects[channel]["OFFSET"].setValue(waveform_parameters["offset"])
        # Assuming WAVEFORM_TYPE is a QComboBox or similar, this line remains unchanged

        self.input_objects[channel]["WAVEFORM_TYPE"].setCurrentText(
            waveform_parameters["waveform_type"]
        )
