from datetime import datetime, timedelta


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
