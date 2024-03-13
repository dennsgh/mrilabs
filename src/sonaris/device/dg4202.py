from typing import List
from unittest.mock import MagicMock

from sonaris.device.data import DataSource
from sonaris.device.device import Device, MockDevice
from sonaris.device.interface import Interface


class DG4202(Device):
    IDN_STRING = "DG4202"
    FREQ_LIMIT = 2e8

    @staticmethod
    def available_waveforms() -> List[str]:
        """
        Returns a list of available waveform types.

        Returns:
            List[str]: List of available waveform types.
        """
        return ["SIN", "SQUARE", "RAMP", "PULSE", "NOISE", "ARB", "DC"]

    @staticmethod
    def available_modes() -> List[str]:
        """
        Returns a list of available modes.

        Returns:
            List[str]: List of available modes.
        """
        return ["off", "sweep", "burst", "mod"]

    def __init__(self, interface: Interface):
        super().__init__(interface)

    def set_waveform(
        self,
        channel: int,
        waveform_type: str = None,
        frequency: float = None,
        amplitude: float = None,
        offset: float = None,
        params: dict = None,
    ) -> None:
        """
        Generates a waveform with the specified parameters. If a parameter is None, its current value is left unchanged.

        Args:
            channel (int): The channel to apply it to
            waveform_type (str, optional): The type of waveform to generate. Defaults to None.
            frequency (float, optional): The frequency of the waveform in Hz. Defaults to None.
            amplitude (float, optional): The amplitude of the waveform. Defaults to None.
            offset (float, optional): The offset of the waveform. Defaults to None.
            params (float, optional): parameter dictionary.
        """
        if params is None:
            params = {}  # Create an empty dictionary if params is None

        channel = channel or params.get("channel")
        waveform_type = waveform_type or params.get("waveform_type")
        # Default frequency to 0.0 if not provided to safely handle comparison
        frequency = frequency if frequency is not None else params.get("frequency", 0.0)
        # Ensure frequency does not exceed the FREQ_LIMIT
        frequency = min(frequency, self.FREQ_LIMIT)
        amplitude = amplitude or params.get("amplitude")
        offset = offset or params.get("offset")
        if waveform_type is not None:
            self.interface.write(f"SOURce{channel}:FUNCtion {waveform_type}")
        if frequency is not None:
            self.interface.write(f"SOURce{channel}:FREQuency:FIXed {frequency}")
        if amplitude is not None:
            self.interface.write(
                f"SOURce{channel}:VOLTage:LEVel:IMMediate:AMPLitude {amplitude}"
            )
        if offset is not None:
            self.interface.write(
                f"SOURce{channel}:VOLTage:LEVel:IMMediate:OFFSet {offset}"
            )

    def turn_off_modes(self, channel: int) -> None:
        """
        Turns off all modes (sweep, burst, modulation) on the device.
        """
        self.interface.write(f"SOURce{channel}:SWEEp:STATe OFF")
        self.interface.write(f"SOURce{channel}:BURSt:STATe OFF")
        self.interface.write(f"SOURce{channel}:MOD:STATe OFF")

    def check_status(self) -> str:
        """
        Checks the status of the device.

        Returns:
            str: The status of the device.
        """
        return self.interface.read("*STB?")

    def output_on_off(self, channel: int, status: bool) -> bool:
        """
        Turns the output of the device on or off.

        Args:
            status (bool): True to turn on the output, False to turn it off.
        """
        command = f"OUTPut{channel} ON" if status else f"OUTPut{channel} OFF"
        self.interface.write(command)

    def set_mode(self, channel: int, mode: str, mod_type: str = None) -> None:
        """
        Sets the mode of the device.

        Args:
            mode (str): The mode to set. Supported values: 'sweep', 'burst', 'mod', 'off'.
            mod_type (str, optional): The modulation type. Required when mode is 'mod'. Defaults to None.
        """
        if isinstance(self.interface, DG4202MockInterface):
            self.interface.write(f"SOURce{channel}:BURSt:STATe OFF")
            self.interface.write(f"SOURce{channel}:MOD:STATe OFF")

        if mode.lower() == "sweep":
            self.interface.write(f"SOURce{channel}:SWEEp:STATe ON")

        elif mode.lower() == "burst":
            self.interface.write(f"SOURce{channel}:BURSt:STATe ON")
        elif mode.lower() == "mod":
            self.interface.write(f"SOURce{channel}:MOD:STATe ON")
            if mod_type:
                self.interface.write(f"SOURce{channel}:MOD:TYPE {mod_type}")
        elif mode.lower() == "off":
            self.turn_off_modes(channel)
        else:
            print("Unsupported mode. Please use 'sweep', 'burst', or 'mod'")

    def set_modulation_mode(self, channel: int, mod_type: str, mod_params: dict):
        """
        Sets the device to modulation mode with the specified parameters.

        Args:
            channel (int): The output channel to set.
            mod_type (str): The type of modulation to apply.
            mod_params (dict): Dictionary of parameters for modulation mode.
                Expected keys are 'SOUR', 'DEPT', 'DEV', 'RATE' etc.
        """
        self.interface.write(f"SOURce{channel}:MOD:STATe ON")
        self.interface.write(f"SOURce{channel}:MOD:TYPE {mod_type}")
        for param in ["SOUR", "DEPT", "DEV", "RATE"]:  # Add more parameters as needed
            if param not in mod_params:
                mod_params[param] = self.interface.read(
                    f"SOURce{channel}:MOD:{mod_type}:{param}?"
                )
            self.interface.write(
                f"SOURce{channel}:MOD:{mod_type}:{param} {mod_params[param]}"
            )

    def set_burst_mode(self, channel: int, burst_params: dict):
        """
        Sets the device to burst mode with the specified parameters.

        Args:
            channel (int): The output channel to set.
            burst_params (dict): Dictionary of parameters for burst mode.
                Expected keys are 'NCYC', 'MODE', 'TRIG', 'PHAS' etc.
        """
        self.interface.write(f"SOURce{channel}:BURSt:STATe ON")
        for param in ["NCYC", "MODE", "TRIG", "PHAS"]:  # Add more parameters as needed
            if param not in burst_params:
                burst_params[param] = self.interface.read(
                    f"SOURce{channel}:BURSt:{param}?"
                )
            self.interface.write(f"SOURce{channel}:BURSt:{param} {burst_params[param]}")

    def set_sweep_mode(self, channel: int, sweep_params: dict):
        """
        Sets the device to sweep mode with the specified parameters.

        Args:
            channel (int): The output channel to set.
            sweep_params (dict): Dictionary of parameters for sweep mode.
                Expected keys are 'START', 'STOP', 'SWEEP'.
        """
        self.interface.write(f"SOURce{channel}:SWEEp:STATe ON")
        for param in [
            "START",
            "STOP",
            "SWEEP",
        ]:  # Add 'RETURN' if there's a corresponding command
            if param not in sweep_params:
                sweep_params[param] = self.interface.read(
                    f"SOURce{channel}:SWEEp:{param}?"
                )
            self.interface.write(f"SOURce{channel}:SWEEp:{param} {sweep_params[param]}")

    def get_mode(self, channel: int):
        """
        Gets the current mode of the device along with its parameters.

        Args:
            channel (int): The output channel to check.

        Returns:
            dict: A dictionary containing the current mode and its parameters.
        """
        sweep_state = self.interface.read(f"SOURce{channel}:SWEEp:STATe?")
        burst_state = self.interface.read(f"SOURce{channel}:BURSt:STATe?")
        mod_state = self.interface.read(f"SOURce{channel}:MOD:STATe?")
        mod_type = (
            self.interface.read(f"SOURce{channel}:MOD:TYPE?")
            if mod_state == "1"
            else None
        )

        mode_params = {}
        mode_params["sweep"] = self.get_sweep_parameters(channel)
        mode_params["burst"] = {}
        mode_params[f"mod ({mod_type})"] = {}
        if sweep_state == "1":
            mode = "sweep"
        elif burst_state == "1":
            mode = "burst"
        elif mod_state == "1":
            mode = f"mod ({mod_type})"
        else:
            mode = "off"

        return {"current_mode": mode, "parameters": mode_params}

    def get_sweep_parameters(self, channel: int) -> dict:
        """
        Retrieves the sweep parameters currently set on the device.

        Args:
            channel (int): The output channel to check.

        Returns:
            dict: A dictionary containing the sweep parameters.
        """
        sweep_params = {}
        sweep_params["FSTART"] = float(
            self.interface.read(f"SOURce{channel}:FREQuency:STaRt?")
        )
        sweep_params["FSTOP"] = float(
            self.interface.read(f"SOURce{channel}:FREQuency:STOP?")
        )
        sweep_params["TIME"] = float(
            self.interface.read(f"SOURce{channel}:SWEEp:TIME?")
        )
        sweep_params["RTIME"] = float(
            self.interface.read(f"SOURce{channel}:SWEEp:RTIMe?")
        )
        sweep_params["HTIME_START"] = float(
            self.interface.read(f"SOURce{channel}:SWEEp:HTIMe:STaRt?")
        )
        sweep_params["HTIME_STOP"] = float(
            self.interface.read(f"SOURce{channel}:SWEEp:HTIMe:STOP?")
        )
        # Add here the command for 'RETURN' when it is known
        # sweep_params['RETURN'] = self.interface.read(f"SOURce{channel}:???")

        return sweep_params

    def set_sweep_parameters(self, channel: int, sweep_params: dict):
        """
        Sets the sweep parameters on the device.

        Args:
            channel (int): The output channel to set.
            sweep_params (dict): Dictionary of parameters for sweep mode.
        """
        self.set_mode(channel, "sweep")
        if sweep_params.get("FSTART") is not None:
            self.interface.write(
                f"SOURce{channel}:FREQuency:STaRt {sweep_params['FSTART']}"
            )
        if sweep_params.get("FSTOP") is not None:
            self.interface.write(
                f"SOURce{channel}:FREQuency:STOP {sweep_params['FSTOP']}"
            )
        if sweep_params.get("TIME") is not None:
            self.interface.write(f"SOURce{channel}:SWEEp:TIME {sweep_params['TIME']}")
        if sweep_params.get("RTIME") is not None:
            self.interface.write(f"SOURce{channel}:SWEEp:RTIMe {sweep_params['RTIME']}")
        if sweep_params.get("HTIME_START") is not None:
            self.interface.write(
                f"SOURce{channel}:SWEEp:HTIMe:STaRt {sweep_params['HTIME_START']}"
            )
        if sweep_params.get("HTIME_STOP") is not None:
            self.interface.write(
                f"SOURce{channel}:SWEEp:HTIMe:STOP {sweep_params['HTIME_STOP']}"
            )

    def get_status(self, channel: int) -> str:
        status = []

        status.append(f"Output: {self.get_output_status(channel)}")
        status.append(f"Current mode: {self.get_mode(channel)}")
        status.append(
            f"Current waveform parameters: {self.get_waveform_parameters(channel)}"
        )

        return ", ".join(status)

    def get_output_status(self, channel: int) -> str:
        return (
            "ON"
            if self.interface.read(f"OUTPut{channel}?").strip() in ["1", "ON"]
            else "OFF"
        )

    def get_waveform_parameters(self, channel: int) -> dict:
        """_summary_

        Args:
            channel (int): _description_

        Returns:
            dict:
            'waveform_type': waveform_type,
            'frequency': frequency,
            'amplitude': amplitude,
            'offset': offset,
        """
        waveform_type = self.interface.read(f"SOURce{channel}:FUNCtion?")
        frequency = self.interface.read(f"SOURce{channel}:FREQuency:FIXed?")
        amplitude = self.interface.read(
            f"SOURce{channel}:VOLTage:LEVel:IMMediate:AMPLitude?"
        )
        offset = self.interface.read(f"SOURce{channel}:VOLTage:LEVel:IMMediate:OFFSet?")

        return {
            "waveform_type": str(waveform_type),
            "frequency": float(frequency),
            "amplitude": float(amplitude),
            "offset": float(offset),
        }

    def is_connection_alive(self) -> bool:
        try:
            _ = self.interface.read("SOURce1:FUNCtion?")
            if _ is None:
                # this is purely to simulate when in hardware mock to disconnect the device (i.e. when sending via the API flask server simulate_kill 'kill' : 'true' (look at notebooks))
                return False
            return True
        except:
            return False


class DG4202Mock(MockDevice, DG4202):
    def __init__(self):
        interface = DG4202MockInterface()
        super().__init__(interface=interface)
        DG4202.__init__(self, interface=interface)
        self.blocked_methods = {
            "set_waveform",
            "turn_off_modes",
            "check_status",
            "output_on_off",
            "set_mode",
            "set_modulation_mode",
            "set_burst_mode",
            "set_sweep_mode",
            "get_mode",
            "get_sweep_parameters",
            "set_sweep_parameters",
            "get_status",
            "get_output_status",
            "get_waveform_parameters",
        }


class DG4202MockInterface(Interface):
    def __init__(self):
        self.state = {
            "*STB?": "0",
            "SOURce1:SWEEp:STATe": "0",
            "SOURce1:BURSt:STATe": "0",
            "SOURce1:MOD:STATe": "0",
            "SOURce1:MOD:TYPE": "none",
            "OUTPut1": "0",
            "SOURce1:FUNCtion": "SIN",
            "SOURce1:FREQuency:FIXed": "375.0",
            "SOURce1:VOLTage:LEVel:IMMediate:AMPLitude": "3.3",
            "SOURce1:VOLTage:LEVel:IMMediate:OFFSet": "0.0",
            "SOURce1:SWEEp:STARt": "0",
            "SOURce1:FREQuency:STOP": "0",
            "SOURce1:FREQuency:STaRt": "0",
            "SOURce1:SWEEp:STOP": "0",
            "SOURce1:SWEEp:TIME": "1.0",
            "SOURce1:SWEEp:HTIMe:STaRt": "0",
            "SOURce1:SWEEp:HTIMe:STOP": "0",
            "SOURce1:SWEEp:RTIMe": "0",
            "SOURce1:SWEEp:SPAC": "0",
            "SOURce1:BURSt:NCYC": "0",
            "SOURce1:BURSt:MODE": "0",
            "SOURce1:BURSt:TRIG": "0",
            "SOURce1:BURSt:PHAS": "0",
            "SOURce1:MOD:SOUR": "0",
            "SOURce1:MOD:DEPT": "0",
            "SOURce1:MOD:DEV": "0",
            "SOURce1:MOD:RATE": "0",
            "SOURce2:SWEEp:STATe": "0",
            "SOURce2:BURSt:STATe": "0",
            "SOURce2:MOD:STATe": "0",
            "SOURce2:MOD:TYPE": "none",
            "OUTPut2": "0",
            "SOURce2:FUNCtion": "SIN",
            "SOURce2:FREQuency:FIXed": "375.0",
            "SOURce2:VOLTage:LEVel:IMMediate:AMPLitude": "3.3",
            "SOURce2:VOLTage:LEVel:IMMediate:OFFSet": "0.0",
            "SOURce2:SWEEp:STARt": "0",
            "SOURce2:FREQuency:STOP": "0",
            "SOURce2:FREQuency:STaRt": "0",
            "SOURce2:SWEEp:STOP": "0",
            "SOURce2:SWEEp:TIME": "1.0",
            "SOURce2:SWEEp:HTIMe:STaRt": "0",
            "SOURce2:SWEEp:HTIMe:STOP": "0",
            "SOURce2:SWEEp:RTIMe": "0",
            "SOURce2:SWEEp:SPAC": "0",
            "SOURce2:BURSt:NCYC": "0",
            "SOURce2:BURSt:MODE": "0",
            "SOURce2:BURSt:TRIG": "0",
            "SOURce2:BURSt:PHAS": "0",
            "SOURce2:MOD:SOUR": "0",
            "SOURce2:MOD:DEPT": "0",
            "SOURce2:MOD:DEV": "0",
            "SOURce2:MOD:RATE": "0",
        }
        mock_resource = MagicMock()
        # Setup any default attributes or return values if necessary
        mock_resource.timeout = None  # Set default value for timeout attribute
        super().__init__(mock_resource)
        self.debug = True

    def write(self, command: str) -> None:
        if command in [
            "OUTPut1 ON",
            "SOURce1:SWEEp:STATe ON",
            "SOURce1:BURSt:STATe ON",
            "SOURce1:MOD:STATe ON",
            "OUTPut2 ON",
            "SOURce2:SWEEp:STATe ON",
            "SOURce2:BURSt:STATe ON",
            "SOURce2:MOD:STATe ON",
        ]:
            command, value = command.split()
            self.state[command] = "1"
        elif command in [
            "OUTPut1 OFF",
            "SOURce1:SWEEp:STATe OFF",
            "SOURce1:BURSt:STATe OFF",
            "SOURce1:MOD:STATe OFF",
            "OUTPut2 OFF",
            "SOURce2:SWEEp:STATe OFF",
            "SOURce2:BURSt:STATe OFF",
            "SOURce2:MOD:STATe OFF",
        ]:
            command, value = command.split()
            self.state[command] = "0"
        else:
            command, value = command.split()
            self.state[command] = value

    def read(self, command: str) -> str:
        if command.endswith("?"):
            command = command[:-1]
        return self.state.get(command, "").split(" ")[-1]


class DG4202DataSource(DataSource):
    def __init__(self, source: DG4202):
        super().__init__(source)
        self.all_parameters = {}
        self.default_dict = {"connected": None}
        self.source: DG4202 = source
        for channel in range(1, 3):
            self.default_dict[f"{channel}"] = {
                "waveform": {
                    "waveform_type": "SIN",
                    "frequency": 0.0,
                    "amplitude": 0.0,
                    "offset": 0.0,
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
                            "HTIME_START": 0,
                            "HTIME_STOP": 0,
                        },
                        "burst": "",
                    },
                },
                "output_status": "OFF",
            }

    def query_data(self) -> dict:
        """
        Get all parameters for each channel from the waveform generator.

        Returns:
            dict: Dictionary containing parameters of the device.
        """
        if self.source:
            is_alive = self.source.is_connection_alive()

            if is_alive:
                for channel in range(1, 3):
                    self.all_parameters[f"{channel}"] = {
                        "waveform": self.source.get_waveform_parameters(channel),
                        "mode": self.source.get_mode(channel),
                        "output_status": self.source.get_output_status(channel),
                    }
                self.all_parameters["connected"] = True

            else:
                self.source = None
                self.all_parameters = self.default_dict
                self.all_parameters["connected"] = False

        else:
            self.all_parameters = self.default_dict
            self.all_parameters["connected"] = False
        return self.all_parameters
