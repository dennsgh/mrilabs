from datetime import datetime, timedelta

from scheduler.timekeeper import Timekeeper


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


def schedule_tasks(
    schedule_times,
    timekeeper: Timekeeper,
    get_task_enum_value,
    is_in_enum,
    QMessageBox,
    self,
):
    """
    Schedule tasks based on the calculated schedule times.
    :param schedule_times: A list of tuples (step, schedule_time) with steps and their schedule times.
    :param timekeeper: The scheduling mechanism (e.g., a timekeeper object) to add jobs to.
    """
    for step, schedule_time in schedule_times:
        task_str = step.get("task")
        parameters = step.get("parameters", {})
        task_name_str = get_task_enum_value(task_str, self.task_enum)
        if not is_in_enum(task_str.strip(), self.task_enum):
            QMessageBox.critical(
                self, "Error Scheduling Task", f"Unknown task: '{task_name_str}'"
            )
            return
        try:
            timekeeper.add_job(task_name_str, schedule_time, kwargs=parameters)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Scheduling Task",
                f"Failed to schedule '{task_name_str}': {e}",
            )
            return  # Stop scheduling further tasks on error
