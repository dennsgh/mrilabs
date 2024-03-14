import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict

from sonaris.defaults import DEFAULT_DATADIR
from sonaris.scheduler.worker import Worker
from sonaris.utils.log import create_numbered_backup, get_logger


class Timekeeper:
    def __init__(
        self,
        persistence_file: Path,
        worker_instance: Worker,
        logger: logging.Logger = None,
        user_callback: Callable = None,
        archive: Path = None,
    ):
        """
        Initializes the Timekeeper class, responsible for managing and scheduling jobs.

        Args:
            persistence_file (Path): Path to the file used for persisting job data.
            worker_instance (Worker): An instance of the Worker class to execute scheduled tasks.
        """
        self.logger = logger or get_logger()
        self.persistence_file = persistence_file
        self.worker = worker_instance
        self.jobs = self.load_jobs()
        self.archive = (
            archive
            or Path(os.getenv("DATA"), "archive.json")
            or DEFAULT_DATADIR / "archive.json"
        )
        self.reload_function_map()
        self.__reschedule_jobs__()
        self.user_callback = user_callback
    def get_archive(self) -> Dict[str, Any]:
        return json.loads(self.archive.read_text())
    def set_callback(self, user_callback: Callable) -> None:
        self.user_callback = user_callback

    def cancel_job(self, job_id: str) -> None:
        """Removes job from worker and erases entry

        Args:
            job_id (str): _description_
        """
        self.worker.remove_scheduled_task(job_id)
        self.remove_job(job_id)

    def clear_archive(self):
        # Clear the JSON file
        try:
            with self.archive.open("w") as file:
                json.dump({}, file)
        except Exception as e:
            self.logger.error(f"Error clearing finished jobs: {e}")

    def load_jobs(self) -> Dict[str, Any]:
        """
        Loads the jobs from the persistence file.

        Returns:
            Dict[str, Any]: A dictionary of jobs indexed by their IDs.
        """
        try:
            with open(self.persistence_file, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_jobs(self) -> None:
        """
        Saves the current jobs to the persistence file.
        """
        with open(self.persistence_file, "w") as file:
            json.dump(self.jobs, file, indent=4)

    def compute_hash(
        self, task_name: str, schedule_time: datetime, *args, **kwargs
    ) -> str:
        """
        Computes a hash for the given task and arguments.

        Args:
            task_name (str): The name of the task.
            *args: Positional arguments for the task.
            **kwargs: Keyword arguments for the task.

        Returns:
            str: A hash string representing the task and arguments.
        """
        args = args or ""
        kwargs = kwargs or ""
        return hashlib.sha256(
            str(f"{task_name}{schedule_time.isoformat()}{args}{kwargs}").encode()
        ).hexdigest()[:12]

    def add_job(self, task_name: str, schedule_time: datetime, **kwargs) -> str:
        """
        Adds a new job to the schedule.

        Args:
            task_name (str): The name of the task to schedule.
            schedule_time (datetime): The time at which the task should be executed.
            **kwargs: Keyword arguments to pass to the task.

        Returns:
            str: The ID of the scheduled job.
        """
        job_id = self.compute_hash(task_name, schedule_time, kwargs)
        self.jobs[job_id] = {
            "task": task_name,
            "created": datetime.now().isoformat(),
            "schedule_time": schedule_time.isoformat(),
            **kwargs,
        }
        self.save_jobs()
        self.logger.info(
            f"Received job {job_id} with task {task_name} to run at {schedule_time}"
        )
        self.schedule_job_to_worker(job_id)
        return job_id

    def schedule_job_to_worker(self, job_id: str) -> None:
        """
        Schedules a job to be executed by the worker.

        Args:
            job_id (str): The ID of the job to schedule.
        """
        job_info = self.jobs[job_id]
        schedule_time = datetime.fromisoformat(job_info["schedule_time"])
        self.worker.__schedule_task__(
            job_info["task"],
            schedule_time,
            job_id,
            self.callback,
            **job_info["kwargs"],
        )

    def reload_function_map(self) -> None:
        """
        Reloads the function map from the Worker instance.
        """
        try:
            for (
                func_identifier,
                func_data,
            ) in self.worker.function_map.function_map.items():
                func = self.worker.function_map.deserialize_func(func_data)
                self.worker.register_task(func, func_identifier)
            self.logger.debug("Function map reloaded.")
        except Exception as e:
            self.logger.error(f"Failed to reload function map: {e}")
            backup_file = create_numbered_backup(self.persistence_file)
            self.logger.info(
                f"Created numbered backup of the function map: {backup_file}"
            )

    def __reschedule_jobs__(self) -> None:
        """
        Reschedules all jobs that are due to run.
        """
        self.logger.debug(f"Found {len(self.jobs)} scheduled.")
        now = datetime.now()
        self.prune()
        for job_id, job_info in self.jobs.items():
            schedule_time = datetime.fromisoformat(job_info["schedule_time"])
            if schedule_time < now:
                schedule_time = now + timedelta(seconds=10)
                self.logger.info(f"Rescheduling job {job_id} to run at {schedule_time}")
            self.worker.__schedule_task__(
                job_info["task"],
                schedule_time,
                job_id,
                self.callback,
                **job_info["kwargs"],
            )

    def archive_job(self, job_id: str, job_info: Dict[str, Any]) -> None:
        """
        Archives a completed job.

        Args:
            job_id (str): The ID of the completed job.
            job_info (Dict[str, Any]): The details of the completed job.
        """
        try:
            if not self.archive.exists():
                # Create the archive file if it doesn't exist
                with open(self.archive, "w") as file:
                    json.dump({}, file)

            with open(self.archive, "r+") as file:
                archived_jobs = json.load(file)
                archived_jobs[job_id] = job_info
                file.seek(0)
                json.dump(archived_jobs, file, indent=4)

            self.logger.info(f"Job {job_id} archived.")
        except Exception as e:
            self.logger.error(f"Failed to archive job {job_id}: {e}")

    def callback(self, job_id: str, result: bool, error_info: str = None) -> None:
        """
        Callback method that is called when a job is completed.

        Args:
            job_id (str): The unique identifier of the job.
            result (bool): The result of the job execution, True if successful, False otherwise.
            error_info (str, optional): The traceback or error information if the job failed.
        """
        # Retrieve the job information, if not found, use an empty dictionary
        job_info = self.jobs.get(job_id, {})

        # Update the job_info dictionary with the result of the execution
        job_info["result"] = result

        # If there is error information (job execution failed), add it to the job_info
        if error_info:
            job_info["error_info"] = error_info

        # Perform job archival and removal
        self.archive_job(
            job_id, job_info
        )  # Assuming you want to archive the job with updated info
        self.remove_job(job_id)

        # Call the user-defined callback if it exists
        if self.user_callback is not None:
            # You might want to pass additional arguments or the updated job_info to your user_callback
            self.user_callback()

    def remove_job(self, job_id: str) -> None:
        """Removes from internal entry, not on worker node!

        Args:
            job_id (str): _description_
        """
        self.jobs.pop(job_id)
        self.save_jobs()
        self.logger.info(f"Job {job_id} removed.")

    def prune(self) -> None:
        """
        Removes jobs that are no longer valid or have passed their schedule time.
        """
        now = datetime.now()
        jobs_to_remove = [
            job_id
            for job_id, job_info in self.jobs.items()
            if datetime.fromisoformat(job_info["schedule_time"]) < now
        ]
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            self.logger.info(f"Pruned job {job_id}")
        self.save_jobs()

    def get_jobs(self) -> Dict[str, Any]:
        """
        Returns the currently scheduled jobs.

        Returns:
            Dict[str, Any]: A dictionary of the scheduled jobs.
        """
        return self.jobs
