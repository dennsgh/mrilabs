from enum import Enum

from features.task_decorator import parameter_constraints
from header import DeviceName
from pages import factory

from device.dg4202 import DG4202

"""
These tasks are used by the scheduler, they are wrappers for the scheduler to call the manager objects.
You will have to point to them under header.py
"""


class TaskName(Enum):
    DG4202_TOGGLE = "Toggle Output"
    DG4202_SET_WAVEFORM = "Set Waveform Parameters"
    DG4202_SET_SWEEP = "Set Sweep Parameters"
    EDUX1002A_AUTO = "Press Auto"

    @staticmethod
    def get_name_enum(task_name_str):
        # First, try looking up by name
        try:
            return TaskName[task_name_str]
        except KeyError:
            pass
        # Next, try looking up by value
        for _, member in TaskName.__members__.items():
            if member.value == task_name_str:
                return member
        return None


@parameter_constraints(channel=(1, 2))
def task_on_off_dg4202(channel: int, status: bool) -> bool:
    factory.dg4202_manager.device.output_on_off(channel=channel, status=status)
    return True


@parameter_constraints(
    frequency=(0.0, float("inf")),
    channel=(1, 2),
    waveform_type=DG4202.available_waveforms(),
    offset=(0, 5),
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


@parameter_constraints(
    channel=(1, 2),
    fstart=(0.0, float("inf")),
    fstop=(0.0, float("inf")),
    time=(0.0, float("inf")),
    rime=(0.0, float("inf")),
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


def task_auto_edux1002a(*args, **kwargs):
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

TASK_USER_INTERFACE_DICTIONARY = {
    DeviceName.DG4202.value: {
        TaskName.DG4202_TOGGLE.value: [
            {
                "type": "QComboBox",
                "label": "Channel",
                "kwarg_label": "channel",
                "options": ["1", "2"],
                "data_type": "int",
            },
            {
                "type": "QComboBox",
                "label": "Switch to",
                "options": ["ON", "OFF"],
                "kwarg_label": "status",
                "data_type": "str",
            },
        ],
        TaskName.DG4202_SET_WAVEFORM.value: [
            {
                "type": "QComboBox",
                "label": "Channel",
                "kwarg_label": "channel",
                "options": ["1", "2"],
                "data_type": "int",
            },
            {
                "type": "QComboBox",
                "label": "Waveform Type",
                "kwarg_label": "waveform_type",
                "options": DG4202.available_waveforms(),
                "data_type": "str",
            },
            {
                "type": "QLineEdit",
                "label": "Frequency (Hz)",
                "kwarg_label": "frequency",
                "data_type": "float",
            },
            {
                "type": "QLineEdit",
                "label": "Amplitude (V)",
                "kwarg_label": "amplitude",
                "data_type": "float",
            },
            {
                "type": "QLineEdit",
                "label": "Offset (V)",
                "kwarg_label": "offset",
                "data_type": "float",
            },
            {
                "type": "QComboBox",
                "label": "Send ON",
                "options": ["False", "True"],
                "kwarg_label": "send_on",
                "data_type": "bool",
            },
        ],
        TaskName.DG4202_SET_SWEEP.value: [
            {
                "type": "QComboBox",
                "label": "Channel",
                "kwarg_label": "channel",
                "options": ["1", "2"],
                "data_type": "int",
            },
            {
                "type": "QLineEdit",
                "label": "Freq Start (Hz)",
                "kwarg_label": "fstart",
                "data_type": "float",
            },
            {
                "type": "QLineEdit",
                "label": "Freq Stop (Hz)",
                "kwarg_label": "fstop",
                "data_type": "float",
            },
            {
                "type": "QLineEdit",
                "label": "Time (s)",
                "kwarg_label": "time",
                "data_type": "float",
            },
            {
                "type": "QLineEdit",
                "label": "Return (ms)",
                "kwarg_label": "rtime",
                "data_type": "float",
            },
            {
                "type": "QLineEdit",
                "label": "Start Hold (ms)",
                "kwarg_label": "htime_start",
                "data_type": "float",
            },
            {
                "type": "QLineEdit",
                "label": "Stop Hold (ms)",
                "kwarg_label": "htime_stop",
                "data_type": "float",
            },
            {
                "type": "QComboBox",
                "label": "Send ON",
                "options": ["False", "True"],
                "kwarg_label": "send_on",
                "data_type": "bool",
            },
        ],
    },
    DeviceName.EDUX1002A.value: {
        TaskName.EDUX1002A_AUTO.value: [
            {
                "type": "QComboBox",
                "label": "Autoscale",
                "kwarg_label": "this is an example, this should match the kwarg on the task function",
                "options": ["True", "False"],
                "data_type": "bool",
            },
        ],
    },
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
