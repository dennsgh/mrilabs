import json
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Optional
import traceback
import yaml
from fastapi import FastAPI

from sonaris.defaults import (
    DATA_SOURCE_NAME,
    DATA_SOURCE_PORT,
    GF_PROVISIONING_DIR,
)
from sonaris.services.dashboards import DS_SONARIS_DATASOURCE,TASK_DASHBOARD
from sonaris.scheduler.timekeeper import Timekeeper
from sonaris.services.service import MultithreadedServer, Service
from sonaris.utils.log import get_logger

logger = get_logger()


class DataSourceService(Service):
    def __init__(
        self,
        timekeeper: Timekeeper,
        port: int = None,
        logger: Optional[Logger] = None,
        name: str = None,
    ):
        super().__init__()
        self.name = str(name) or str(DATA_SOURCE_NAME)
        self.timekeeper = timekeeper
        self.port = port or DATA_SOURCE_PORT
        self.logger = logger or get_logger()
        self.app = FastAPI(title="Sonaris Data Source Service")
        self.setup_routes()

        # Prepare the Uvicorn config here
        self.server = MultithreadedServer(
            app=self.app, port=self.port, log_level="info"
        )

    @staticmethod
    def get_data_source_manifest(
        host="http://host.docker.internal", port=DATA_SOURCE_PORT, name=DATA_SOURCE_NAME
    ):
        # Update the data source type to match the plugin being used (e.g., for Grafana Infinity)
        return DS_SONARIS_DATASOURCE(str(host),str(port))

    @staticmethod
    def get_dashboard_manifest(
        host="http://host.docker.internal", port=DATA_SOURCE_PORT, name=DATA_SOURCE_NAME

    ):
        try:
            return json.loads(TASK_DASHBOARD)
        except Exception as e:
            logger.error(f"Error loading TASK_DASHBOARD: {e}")
            logger.error(f"{traceback.format_exc()}")
            return {}
    @staticmethod
    def dashboard_config():
        return {
            "apiVersion":
            1,
            "providers": [{
                "name": "dashboards",
                "orgId": 1,
                "folderUid": "",
                "type": "file",
                "disableDeletion": True,
                "updateIntervalSeconds": 15,
                "allowUiUpdates": False,
                "options": {
                    "path": "/etc/grafana/provisioning/dashboards",
                    "foldersFromFilesStructure": True,
                },
            }],
        }

    def write_provisioning_files(
        self, provisioning_dir: str
    ):
        # Ensure directories exist
        datasources_dir = Path (provisioning_dir or GF_PROVISIONING_DIR ) / "datasources"
        dashboards_dir = Path(provisioning_dir or GF_PROVISIONING_DIR ) / "dashboards"

        datasources_dir.mkdir(parents=True, exist_ok=True)
        dashboards_dir.mkdir(parents=True, exist_ok=True)

        # Data source file
        data_source_path = datasources_dir / "datasource.yml"
        with open(data_source_path, "w") as file:
            yaml.dump(self.get_data_source_manifest(), file)

        # Dashboard file
        dashboard_manifest = self.get_dashboard_manifest()
        dashboard_path = dashboards_dir / f"{self.name}.json"
        with open(dashboard_path, "w") as file:
            json.dump(dashboard_manifest, file)

        dashboard_provisioning_path = dashboards_dir / "config.yml"
        with open(dashboard_provisioning_path, "w") as file:
            yaml.dump(self.dashboard_config(), file)

        # Log or handle the fact that files are written
        logger.info(f"Datasource files written: {data_source_path}")
        logger.info(f"Dashboard files written: {dashboard_path}")


    def setup_routes(self):

        @self.app.get("/jobs")
        async def get_jobs():
            # Fetch jobs data
            jobs_data = self.timekeeper.get_jobs()  # This returns a dict of jobs

            # Check if jobs_data is empty and return a message if true
            if not jobs_data:
                return [{"task": "No tasks found"}]

            # Otherwise, format and return jobs data
            formatted_jobs = [
                {
                    "id":
                    job_id,
                    "timestamp":
                    datetime.strptime(job["created"],
                                    "%Y-%m-%dT%H:%M:%S.%f").isoformat(),
                    "task":
                    job["task"],
                    "result":
                    job.get(
                        "result",
                        "Pending"),  # Default to "Pending" if result is not set
                    "kwargs":
                    job["kwargs"],
                    "schedule_time":
                    datetime.strptime(job["schedule_time"],
                                    "%Y-%m-%dT%H:%M:%S.%f"),
                } for job_id, job in jobs_data.items()
            ]
            return formatted_jobs

        @self.app.get("/archive")
        async def get_archive():
            # Fetch archive data
            archive_data = self.timekeeper.get_archive(
            )  # This returns a dict of archived jobs

            # Check if archive_data is empty and return a message if true
            if not archive_data:
                return [{"task": "No tasks found"}]

            # Otherwise, format and return archive data
            formatted_archive = [
                {
                    "id":
                    archive_id,
                    "timestamp":
                    datetime.strptime(archive["created"],
                                    "%Y-%m-%dT%H:%M:%S.%f").isoformat(),
                    "task":
                    archive["task"],
                    "result":
                    archive.get("result", "Completed"
                                ),  # Default to "Completed" if result is not set
                    "kwargs":
                    archive["kwargs"],
                    "schedule_time":
                    datetime.strptime(archive["schedule_time"],
                                    "%Y-%m-%dT%H:%M:%S.%f"),
                } for archive_id, archive in archive_data.items()
            ]
            return formatted_archive


    def start(self):
        self.logger.info("Starting DataSourceService...")
        self.server.start()
        self.logger.info("DataSourceService started.")

    def stop(self):
        self.logger.info("Stopping DataSourceService...")
        self.server.stop()
        self.logger.info("DataSourceService stopped.")
