from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from pages.templates import BasePage
from device.dg4202 import DG4202
from pages import factory
from datetime import datetime, timedelta

NOT_FOUND_STRING = 'Device not found!'
TIMER_INTERVAL = 1000.  # in ms
TIMER_INTERVAL_S = TIMER_INTERVAL / 1000.  # in ms

DEFAULT_TAB_STYLE = {'height': '30px', 'padding': '2px'}


class DG4202Page(BasePage):

    def check_connection(self) -> bool:

        self.my_generator = factory.dg4202_manager.create_dg4202()
        if self.my_generator is not None:
            is_alive = self.my_generator.is_connection_alive()
            if not is_alive:
                self.my_generator = None
            return is_alive
        return False

    def get_all_parameters(self) -> bool:
        """
        Get all parameters for each channel from the waveform generator.

        Returns:
            bool: True if parameters are successfully retrieved, False otherwise.
        """
        if self.check_connection():
            for channel in range(1, self.channel_count + 1):
                self.all_parameters[f"{channel}"] = {
                    "waveform": self.my_generator.get_waveform_parameters(channel),
                    "mode": self.my_generator.get_mode(channel),
                    "output_status": self.my_generator.get_output_status(channel)
                }
            self.all_parameters["connected"] = True
            return True
        else:
            self.my_generator = None
            for channel in range(1, self.channel_count + 1):
                self.all_parameters[f"{channel}"] = {
                    "waveform": {
                        "waveform_type": "SIN",
                        "frequency": 0.,
                        "amplitude": 0.,
                        "offset": 0.,
                    },
                    "mode": {
                        "current_mode": "error",
                        "parameters": {
                            "off": "",
                            "sweep": {
                                "FSTART": 0,
                                "FSTOP": 0,
                                "TIME": 0,
                                "RTIME": 0,
                            },
                            "burst": "",
                            "off": "",
                        }
                    },
                    "output_status": "OFF"
                }
            self.all_parameters["connected"] = False
            return False

    def __init__(self, parent=None, args_dict: dict = None):
        super().__init__(parent=parent)
        self.args_dict = args_dict
        self.channel_count = 2
        self.link_channel = False
        self.all_parameters = {}
        # Create widgets
        self.get_all_parameters()
        self.create_widgets()
        # Create layout using the widgets
        self.create_layout()
        self.setLayout(self.main_layout)

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
                "sweep_control": sweep_control
            }

    def create_layout(self):
        self.main_layout = QVBoxLayout()

        self.connection_status_label = QLabel(
            "Connection Status:")  # Placeholder for connection status
        self.main_layout.addWidget(self.connection_status_label)
        self.status_label = QLabel("")
        self.main_layout.addWidget(self.status_label)
        for channel, widgets in self.controls.items():
            # Add main controls for the channel

            tab_widget = QTabWidget()
            tab_widget.addTab(widgets["waveform_control"], "Default")
            tab_widget.addTab(widgets["sweep_control"], "Sweep")
            self.main_layout.addWidget(tab_widget)
            tab_widget.currentChanged.connect(self.on_tab_changed)
            self.main_layout.addWidget(widgets["main_controls"])

    def generate_main_controls(self, channel: int) -> QWidget:
        # Setting up Timer Modal (Dialog)
        timer_modal = QDialog(self)
        timer_modal.setWindowTitle("Timer")

        timer_layout = QVBoxLayout()

        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration"))
        duration_input = QLineEdit()
        duration_layout.addWidget(duration_input)

        timer_units = QComboBox()
        timer_units.addItems(['ms', 's', 'm', 'h'])
        duration_layout.addWidget(timer_units)
        timer_layout.addLayout(duration_layout)

        # ... (more widgets and layouts can be added in a similar manner)

        timer_modal.setLayout(timer_layout)

        # Setting up Scheduler Modal (Dialog)
        scheduler_modal = QDialog(self)
        scheduler_modal.setWindowTitle("Scheduler")

        # ... (similarly, add layouts and widgets for this modal)

        # Setting up main layout
        main_layout = QVBoxLayout()

        control_layout = QHBoxLayout()
        # Adding tabs for modes
        # Add more tabs as needed
        output_btn = QPushButton(f"Output CH{channel}")
        control_layout.addWidget(output_btn)

        timer_btn = QPushButton(f"Timer CH{channel}")
        control_layout.addWidget(timer_btn)

        scheduler_btn = QPushButton(f"Scheduler CH{channel}")
        control_layout.addWidget(scheduler_btn)
        # ... (more buttons/widgets to be added)

        main_layout.addLayout(control_layout)

        # Create a QWidget to return
        main_controls_widget = QWidget()
        main_controls_widget.setLayout(main_layout)
        return main_controls_widget

    def generate_sweep_control(self, channel):
        container_widget = QWidget()
        layout = QHBoxLayout()

        # Create widgets and add them to the layout
        # Example:
        sweep_duration_edit = QLineEdit()
        layout.addWidget(sweep_duration_edit)

        # TODO: Add other components for sweep controls, plot, etc.
        container_widget.setLayout(layout)
        return container_widget

    def generate_waveform_control(self, channel: int) -> QWidget:
        """
        Generate the control components for the waveform mode.

        Parameters:
            channel (int): The channel number.

        Returns:
            QWidget: The widget containing the waveform control components.
        """

        # Create a container for this control
        channel_widget = QWidget()
        channel_layout = QHBoxLayout()

        # Left Column (using a form layout for simplicity)
        left_column_layout = QFormLayout()

        # Create dropdown for waveform type
        waveform_type = QComboBox()
        # This assumes DG4202.available_waveforms() returns a list of strings
        waveform_type.addItems(DG4202.available_waveforms())
        left_column_layout.addRow(f"Waveform Type CH{channel}", waveform_type)

        # Create input for Frequency
        freq_input = QLineEdit(str(self.all_parameters[f"{channel}"]["waveform"]["frequency"]))
        left_column_layout.addRow("Frequency (Hz)", freq_input)

        # Create input for Amplitude
        amp_input = QLineEdit(str(self.all_parameters[f"{channel}"]["waveform"]["amplitude"]))
        left_column_layout.addRow("Amplitude (V)", amp_input)

        # Create input for Offset
        offset_input = QLineEdit(str(self.all_parameters[f"{channel}"]["waveform"]["offset"]))
        left_column_layout.addRow("Offset (V)", offset_input)

        # Create a button for Set Waveform and connect it to on_update_waveform slot
        set_waveform_button = QPushButton(f"Set Waveform CH{channel}")
        set_waveform_button.clicked.connect(
            lambda: self.on_update_waveform(channel, waveform_type.currentText(
            ), float(freq_input.text()), float(amp_input.text()), float(offset_input.text())))
        left_column_layout.addRow(set_waveform_button)

        # Right Column (Waveform Plot)
        # NOTE: Use a library like pyqtgraph or matplotlib for the plot.
        # Placeholder label for now
        right_column_layout = QVBoxLayout()
        waveform_plot_placeholder = QLabel("Waveform Plot Here")
        right_column_layout.addWidget(waveform_plot_placeholder,
                                      alignment=Qt.AlignmentFlag.AlignCenter)

        # Add the columns to the main layout
        left_widget = QWidget()
        left_widget.setLayout(left_column_layout)
        right_widget = QWidget()
        right_widget.setLayout(right_column_layout)

        channel_layout.addWidget(left_widget)
        channel_layout.addWidget(right_widget)

        channel_widget.setLayout(channel_layout)

        return channel_widget

    # You can add other methods, slots, signals as required for handling events, callbacks, etc.

    def on_tab_changed(self, index):
        # Placeholder for an API call. Replace with actual logic later.
        if index == 0:  # Assuming 0 is the index for the "Sweep" tab
            pass  # API call for "Sweep"
        elif index == 1:  # Assuming 1 is the index for the "Waveform" tab
            pass  # API call for "Waveform"
        # Add more conditions for other tabs

        # Connect the signal

    def on_update_waveform(self, channel: int, waveform_type: str, frequency: float,
                           amplitude: float, offset: float):
        """
        Update the waveform parameters and plot.

        Parameters:
            channel (int): The channel number.
            waveform_type (str): The selected waveform type.
            frequency (float): The selected frequency.
            amplitude (float): The selected amplitude.
            offset (float): The selected offset.
        """

        if self.get_all_parameters():
            frequency = frequency or float(
                self.all_parameters[f"{channel}"]["waveform"]["frequency"])
            amplitude = amplitude or float(
                self.all_parameters[f"{channel}"]["waveform"]["amplitude"])
            offset = offset or float(self.all_parameters[f"{channel}"]["waveform"]["offset"])
            waveform_type = waveform_type or self.all_parameters[f"{channel}"]["waveform"][
                "waveform_type"]

            # If a parameter is not set, pass the current value
            self.my_generator.set_waveform(channel, waveform_type, frequency, amplitude, offset)

            if self.link_channel:
                self.my_generator.set_waveform(2 if channel == 1 else 1, waveform_type, frequency,
                                               amplitude, offset)

            # Update some status label or log if you have one
            status_string = f"[{datetime.now().isoformat()}] Waveform updated."
            # Assuming you have a status_label in your UI
            self.status_label.setText(status_string)

            # If you were using a library like pyqtgraph or matplotlib for the plot, you would update the graph here
            # For the sake of example, I'm adding a comment
            # figure = plotter.plot_waveform(waveform_type, frequency, amplitude, offset)
            # self.waveform_plot.update_figure(figure)

        else:
            # Update some status label or log if you have one
            self.status_label.setText(NOT_FOUND_STRING)
