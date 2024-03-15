from datetime import datetime, timedelta
from enum import Enum

from sonaris import factory
from sonaris.defaults import DeviceName
from sonaris.device.dg4202 import DG4202
from sonaris.tasks.task_decorator import parameter_annotations, parameter_constraints

"""
These tasks are used by the scheduler, they are wrappers for the scheduler to call the manager objects.
You will have to point to them under header.py
"""


class TaskName(Enum):
    DG4202_TOGGLE = "Toggle Output"
    DG4202_SET_WAVEFORM = "Set Waveform Parameters"
    DG4202_SET_SWEEP = "Set Sweep Parameters"
    EDUX1002A_AUTO = "Press Auto"


@parameter_constraints(channel=(1, 2), output=["ON", "OFF"])
def task_on_off_dg4202(channel: int, output: bool) -> bool:
    factory.dg4202_manager.device.output_on_off(
        channel=channel,
        status=output,  # the decorator above will be handled by ui_factory.py
    )
    return True


@parameter_annotations(
    frequency="Hz",
    offset="V",
    amplitude="V",
)
@parameter_constraints(
    frequency=(0.0, DG4202.FREQ_LIMIT),
    channel=[1, 2],  # decorating with list means forced options
    waveform_type=DG4202.available_waveforms(),
    offset=(0.0, 5.0),
    amplitude=(0.0, 5.0),
)
def task_set_waveform_parameters(
    channel: int,
    send_on: bool,
    waveform_type: str,
    amplitude: float,
    frequency: float,
    offset: float,
) -> bool:
    factory.dg4202_manager.device.set_waveform(
        channel=channel,
        waveform_type=waveform_type,
        amplitude=amplitude,
        frequency=frequency,
        params=None,
        offset=offset,
    )
    if send_on:
        factory.dg4202_manager.device.output_on_off(channel, True)
    return True


@parameter_annotations(
    fstart="Hz",
    fstop="Hz",
    time="s",
    rtime="ms",
    htime_start="ms",
    htime_stop="ms",
)
@parameter_constraints(
    channel=[1, 2],
    fstart=(0.0, DG4202.FREQ_LIMIT),
    fstop=(0.0, DG4202.FREQ_LIMIT),
    time=(0.0, float("inf")),
    rtime=(0.0, float("inf")),
    htime_start=(0.0, float("inf")),
    htime_stop=(0.0, float("inf")),
)
def task_set_sweep_parameters(
    channel: int,
    send_on: bool,
    fstart: float,
    fstop: float,
    time: float,
    rtime: float = 0,
    htime_start: float = 0,
    htime_stop: float = 0,
) -> bool:
    params = {
        "FSTART": fstart,
        "FSTOP": fstop,
        "TIME": time,
        "RTIME": rtime,
        "HTIME_START": htime_start,
        "HTIME_STOP": htime_stop,
    }
    factory.dg4202_manager.device.set_sweep_parameters(
        channel=channel, sweep_params=params
    )
    if send_on:
        factory.dg4202_manager.device.output_on_off(channel, True)
    return True


@parameter_constraints(press=["OK"])
def task_auto_edux1002a(press: str):
    # for testing, kwarg_value means nothing
    factory.edux1002a_manager.device.autoscale()
    return True


"""
The task list is read by the job_scheduler module and app.py to register the task and render the UI.
"""

TASK_LIST_DICTIONARY = {
    DeviceName.DG4202.value: {
        TaskName.DG4202_TOGGLE.value: task_on_off_dg4202,
        TaskName.DG4202_SET_WAVEFORM.value: task_set_waveform_parameters,
        TaskName.DG4202_SET_SWEEP.value: task_set_sweep_parameters,
    },
    DeviceName.EDUX1002A.value: {TaskName.EDUX1002A_AUTO.value: task_auto_edux1002a},
}


def get_tasks(flatten: bool = False) -> dict:
    """Returns the dict of { device : { task-name : func_pointer , ..} ..}

    Returns:
        dict: dictionary containing devices and its tasks.
    """
    if flatten:
        return {
            inner_key: value
            for outer_dict in TASK_LIST_DICTIONARY.values()
            for inner_key, value in outer_dict.items()
        }
    return TASK_LIST_DICTIONARY


def calculate_schedule_times(steps):
    """
    Calculate the schedule times for each step based on wait and at_time keys.
    :param steps: A list of step dictionaries from the experiment configuration.
    :return: A list of tuples (step, schedule_time) with calculated schedule times.
    """
    last_schedule_time = datetime.now()  # Initialize with the current time
    schedule_times = []

    for step in steps:
        if "at_time" in step:
            at_time = timedelta(seconds=step["at_time"])
            schedule_time = datetime.now() + at_time
        else:
            wait_time = timedelta(seconds=step.get("wait", 0))
            schedule_time = last_schedule_time + wait_time

        schedule_times.append((step, schedule_time))
        last_schedule_time = schedule_time  # Update for the next iteration

    return schedule_times
