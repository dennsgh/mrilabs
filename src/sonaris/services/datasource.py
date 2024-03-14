from sonaris.utils.log import get_logger
from fastapi import FastAPI
from pathlib import Path
from typing import Optional
from sonaris.scheduler.timekeeper import Timekeeper
from logging import Logger
from sonaris.defaults import DATA_SOURCE_PORT, DATA_SOURCE_NAME, GF_DASHBOARDS_DIR, GF_DATASOURCES_DIR

from sonaris.services.service import MultithreadedServer,Service
import yaml
import json

logger = get_logger()

class DataSourceService(Service):
    def __init__(self, timekeeper: Timekeeper, port: int = None, logger: Optional[Logger] = None, name:str = None):
        super().__init__()
        self.name = str(name) or str(DATA_SOURCE_NAME)
        self.timekeeper = timekeeper
        self.port = port or DATA_SOURCE_PORT
        self.logger = logger or get_logger()
        self.app = FastAPI(title="Sonaris Data Source Service")
        self.setup_routes()

        # Prepare the Uvicorn config here
        self.server = MultithreadedServer(app=self.app, port=self.port, log_level="info")

    @staticmethod
    def get_data_source_manifest(host="localhost", port=DATA_SOURCE_PORT,name=DATA_SOURCE_NAME):
        return {
            "apiVersion": 1,
            "datasources": [
                {
                    "name": name,
                    "type": "grafana-simple-json-datasource",
                    "access": "proxy",
                    "url": f"http://{host}:{port}",
                    "isDefault": True,
                    "jsonData": {},
                    "secureJsonFields": {}
                }
            ]
        }
    @staticmethod
    def get_dashboard_manifest():
        return {
            "dashboard": {
                "id": None,
                "uid": None,
                "title": "Sonaris Data",
                "panels": [
                    {
                        "type": "table",
                        "title": "Archive",
                        "datasource": "SimpleDataSource",
                        "targets": [
                            {
                                "target": "archive",
                                "refId": "A"
                            }
                        ],
                        "transformations": [
                            {
                                "id": "json",
                                "options": {}
                            }
                        ]
                    },
                    {
                        "type": "table",
                        "title": "Jobs",
                        "datasource": "SimpleDataSource",
                        "targets": [
                            {
                                "target": "jobs",
                                "refId": "B"
                            }
                        ],
                        "transformations": [
                            {
                                "id": "json",
                                "options": {}
                            }
                        ]
                    }
                ]
            },
            "overwrite": False
        }
    def write_provisioning_files(self, datasources_dir: Path =  None, dashboards_dir: Path = None):
        # Ensure directories exist
        datasources_dir = datasources_dir or GF_DATASOURCES_DIR
        dashboards_dir = dashboards_dir or GF_DASHBOARDS_DIR
        
        datasources_dir.mkdir(parents=True, exist_ok=True)
        dashboards_dir.mkdir(parents=True, exist_ok=True)

        # Data source file
        data_source_path = datasources_dir / 'datasource.yml'
        with open(data_source_path, 'w') as file:
            yaml.dump(self.get_data_source_manifest(), file)

        # Dashboard file
        dashboard_manifest = self.get_dashboard_manifest()
        dashboard_path = dashboards_dir / f'{self.name}.json'
        with open(dashboard_path, 'w') as file:
            json.dump(dashboard_manifest, file)

        # Log or handle the fact that files are written
        logger.info(f"Datasource files written: {data_source_path}")
        logger.info(f"Dashboard files written: {dashboard_path}")
    def setup_routes(self):
        @self.app.get("/jobs")
        def get_jobs():
            # Directly return the timekeeper jobs data as JSON
            return self.timekeeper.get_jobs()

        @self.app.get("/archive")
        def get_archive():
            # Assuming Timekeeper has a method to get archive data
            return self.timekeeper.get_archive()

    def start(self):
        self.logger.info("Starting DataSourceService...")
        self.server.start()
        self.logger.info("DataSourceService started.")

    def stop(self):
        self.logger.info("Stopping DataSourceService...")
        self.server.stop()
        self.logger.info("DataSourceService stopped.")