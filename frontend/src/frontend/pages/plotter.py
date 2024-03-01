from typing import Optional

import numpy as np
from PyQt6.QtCharts import QChart, QLineSeries


def plot_waveform(
    waveform_type: Optional[str] = None,
    frequency: Optional[float] = None,
    amplitude: Optional[float] = None,
    offset: Optional[float] = None,
    params: dict = None,
) -> QChart:
    """
    Generate and plot different types of waveforms.

    Parameters:
        waveform_type (str): Type of waveform to generate ('SIN', 'SQUARE', 'RAMP', 'PULSE', 'NOISE', 'ARB', or 'DC').
        frequency (float): Frequency of the waveform.
        amplitude (float): Amplitude of the waveform.
        offset (float): Offset of the waveform.
        params (dict, optional): Optional dictionary containing waveform parameters. If provided, the individual parameters
                                 will be extracted from this dictionary. Defaults to None.

    Returns:
        figure (plotly.graph_objs.Figure): Plotly figure object containing the generated waveform plot.
    """
    if params is not None:
        # If parameters are provided as a dictionary, extract the values
        frequency = float(params["frequency"])
        amplitude = float(params["amplitude"])
        offset = float(params["offset"])
        waveform_type = str(params["waveform_type"])

    # Generate x values from 0 to 1 with 1000 points
    # Assuming one full period of the waveform, change 1/frequency to display multiple periods if required.
    if isinstance(frequency, float) and frequency == 0.0:
        x_values = np.linspace(0, 1, 1000)
    else:
        x_values = np.linspace(0, 4 / frequency, 1000)
    # Generate y values based on the waveform type
    if waveform_type == "SIN":
        y_values = amplitude * np.sin(2 * np.pi * frequency * x_values) + offset
    elif waveform_type == "SQUARE":
        y_values = (
            amplitude * np.sign(np.sin(2 * np.pi * frequency * x_values)) + offset
        )
    elif waveform_type == "RAMP":
        y_values = (
            amplitude
            * (2 * (x_values * frequency - np.floor(x_values * frequency + 0.5)))
            + offset
        )
    elif waveform_type == "PULSE":
        y_values = amplitude * ((x_values * frequency) % 1 < 0.5) + offset
    elif waveform_type == "NOISE":
        y_values = np.random.normal(0, amplitude, len(x_values)) + offset
    elif waveform_type == "ARB":
        # For an arbitrary waveform, you need to define your own function
        y_values = (
            amplitude * np.sin(2 * np.pi * frequency * x_values) + offset
        )  # Placeholder function
    elif waveform_type == "DC":
        y_values = np.full_like(x_values, amplitude + offset)
    else:
        y_values = np.zeros_like(x_values)

    return x_values, y_values


def plot_sweep(
    start_frequency: Optional[float] = None,
    stop_frequency: Optional[float] = None,
    duration: Optional[float] = None,
    rtime: Optional[float] = None,
    htime_start: Optional[float] = None,
    htime_stop: Optional[float] = None,
    params: dict = None,
) -> QChart:
    """
    Generate and plot a frequency sweep.

    Parameters:
        start_frequency (float): Starting frequency of the sweep.
        stop_frequency (float): Stopping frequency of the sweep.
        duration (float): Duration of the sweep.
        rtime (float, optional): Return Time for the sweep.
        htime_start (float, optional): Hold Time Start for the sweep.
        htime_stop (float, optional): Hold Time End for the sweep.
        params (dict, optional): Optional dictionary containing sweep parameters. If provided, the individual parameters
                                 will be extracted from this dictionary. Defaults to None.

    Returns:
        figure (plotly.graph_objs.Figure): Plotly figure object containing the generated sweep plot.
    """
    if params is not None:
        # If parameters are provided as a dictionary, extract the values
        start_frequency = float(params.get("FSTART", start_frequency))
        stop_frequency = float(params.get("FSTOP", stop_frequency))
        duration = float(params.get("TIME", duration))
        rtime = float(params.get("RTIME", rtime))
        htime_start = float(params.get("HTIME_START", htime_start))
        htime_stop = float(params.get("HTIME_STOP", htime_stop))

    # Calculate the number of samples based on the provided duration
    num_samples = int(1000 * duration)  # Convert to samples

    # Ensure that the number of samples is non-negative
    if num_samples < 0:
        num_samples = 0

    # Generate time values based on the number of samples
    t_values = np.linspace(0, duration, num_samples)

    # Apply Hold Time
    if htime_start is not None and htime_stop is not None:
        num_samples_start = int(1000 * htime_start)
        num_samples_hold = int(1000 * (htime_stop - htime_start))
        num_samples_end = int(1000 * (duration - htime_stop))

        # Ensure non-negative number of samples
        num_samples_start = max(num_samples_start, 0)
        num_samples_hold = max(num_samples_hold, 0)
        num_samples_end = max(num_samples_end, 0)

        # Generate time values for hold time
        t_values = np.concatenate(
            [
                np.linspace(0, htime_start, num_samples_start),
                np.linspace(htime_start, htime_stop, num_samples_hold),
                np.linspace(htime_stop, duration, num_samples_end),
            ]
        )

    # Generate a linearly increasing frequency array
    frequency_values = np.linspace(start_frequency, stop_frequency, len(t_values))

    # Generate y values based on the time-varying frequency
    y_values = np.sin(
        2 * np.pi * np.cumsum(frequency_values) * np.mean(np.diff(t_values))
    )

    # Create a plotly figure with t (time) and y values
    series = QLineSeries()
    for t, y in zip(t_values, y_values):
        series.append(t, y)
    return t_values, y_values
