import numpy as np
import plotly.graph_objs as go
from typing import Union, Optional, Dict

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCharts import QChart, QChartView, QLineSeries
from PyQt6.QtCore import Qt


def plot_waveform(waveform_type: Optional[str] = None,
                  frequency: Optional[float] = None,
                  amplitude: Optional[float] = None,
                  offset: Optional[float] = None,
                  params: dict = None) -> QChart:
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
    if waveform_type == 'SIN':
        y_values = amplitude * np.sin(2 * np.pi * frequency * x_values) + offset
    elif waveform_type == 'SQUARE':
        y_values = amplitude * np.sign(np.sin(2 * np.pi * frequency * x_values)) + offset
    elif waveform_type == 'RAMP':
        y_values = amplitude * (
            2 * (x_values * frequency - np.floor(x_values * frequency + 0.5))) + offset
    elif waveform_type == 'PULSE':
        y_values = amplitude * ((x_values * frequency) % 1 < 0.5) + offset
    elif waveform_type == 'NOISE':
        y_values = np.random.normal(0, amplitude, len(x_values)) + offset
    elif waveform_type == 'ARB':
        # For an arbitrary waveform, you need to define your own function
        y_values = amplitude * np.sin(
            2 * np.pi * frequency * x_values) + offset  # Placeholder function
    elif waveform_type == 'DC':
        y_values = amplitude + offset
    else:
        y_values = np.zeros_like(x_values)

    return x_values, y_values


def plot_sweep(start_frequency: Optional[float] = None,
               stop_frequency: Optional[float] = None,
               duration: Optional[float] = None,
               params: dict = None) -> QChart:
    """
    Generate and plot a frequency sweep.

    Parameters:
        start_frequency (float): Starting frequency of the sweep.
        stop_frequency (float): Stopping frequency of the sweep.
        duration (float): Duration of the sweep.
        params (dict, optional): Optional dictionary containing sweep parameters. If provided, the individual parameters
                                 will be extracted from this dictionary. Defaults to None.

    Returns:
        figure (plotly.graph_objs.Figure): Plotly figure object containing the generated sweep plot.
    """
    if params is not None:
        # If parameters are provided as a dictionary, extract the values
        start_frequency = float(params["FSTART"])
        stop_frequency = float(params["FSTOP"])
        duration = float(params["TIME"])

    # Generate time values based on duration with 1000 points
    t_values = np.linspace(0, duration, 1000)

    # Generate a linearly increasing frequency array
    frequency_values = np.linspace(start_frequency, stop_frequency, len(t_values))

    # Generate y values based on the time-varying frequency
    y_values = np.sin(2 * np.pi * np.cumsum(frequency_values) * np.mean(np.diff(t_values)))

    # Create a plotly figure with t (time) and y values
    series = QLineSeries()
    for t, y in zip(t_values, y_values):
        series.append(t, y)
    return t_values, y_values