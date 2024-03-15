import json
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI

from sonaris.defaults import (
    DATA_SOURCE_NAME,
    DATA_SOURCE_PORT,
    GF_DASHBOARDS_DIR,
    GF_DATASOURCES_DIR,
)
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
        return {
            "apiVersion": 1,
            "datasources": [
                {
                    "id": 1,
                    "uid": "P3E0B65AA66943F6C",
                    "orgId": 1,
                    "name": "SonarisDataSource",
                    "type": "yesoreyeram-infinity-datasource",
                    "url": f"{host}:{port}",
                    "basicAuth": "false",
                    "basicAuthUser": "",
                    "isDefault": "true",
                    "jsonData": {
                        "global_queries": [
                            {
                                "name": "task archive",
                                "id": "archive",
                                "query": {
                                    "refId": "my-query-1",
                                    "type": "json",
                                    "source": "url",
                                    "data": "",
                                    "root_selector": "",
                                    "columns": [],
                                    "filters": [],
                                    "format": "as-is",
                                    "url": f"{host}:{port}/archive",
                                    "url_options": {"method": "GET", "data": ""},
                                },
                            },
                            {
                                "name": "job list",
                                "id": "jobs",
                                "query": {
                                    "refId": "my-query-2",
                                    "type": "json",
                                    "source": "url",
                                    "data": "",
                                    "root_selector": "",
                                    "columns": [],
                                    "filters": [],
                                    "format": "table",
                                    "url": f"{host}:{port}/jobs",
                                    "url_options": {"method": "GET", "data": ""},
                                },
                            },
                        ],
                        "refData": [],
                    },
                    "readOnly": "true",
                }
            ],
        }

    @staticmethod
    def get_dashboard_manifest(
        host="http://host.docker.internal", port=DATA_SOURCE_PORT, name=DATA_SOURCE_NAME
    ):
        return {
            "annotations": {
                "list": [
                    {
                        "builtIn": 1,
                        "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                        "enable": "true",
                        "hide": "true",
                        "iconColor": "rgba(0, 211, 255, 1)",
                        "name": "Annotations & Alerts",
                        "type": "dashboard",
                    }
                ]
            },
            "editable": "true",
            "fiscalYearStartMonth": 0,
            "graphTooltip": 0,
            "id": 1,
            "links": [],
            "panels": [
                {
                    "datasource": {
                        "type": "yesoreyeram-infinity-datasource",
                        "uid": "P3E0B65AA66943F6C",
                    },
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "custom": {
                                "axisBorderShow": "false",
                                "axisCenteredZero": "false",
                                "axisColorMode": "text",
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 0,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": "false",
                                    "tooltip": "false",
                                    "viz": "false",
                                },
                                "insertNulls": "false",
                                "lineInterpolation": "linear",
                                "lineWidth": 1,
                                "pointSize": 5,
                                "scaleDistribution": {"type": "linear"},
                                "showPoints": "auto",
                                "spanNulls": "false",
                                "stacking": {"group": "A", "mode": "none"},
                                "thresholdsStyle": {"mode": "off"},
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "red", "value": 80},
                                ],
                            },
                        },
                        "overrides": [],
                    },
                    "gridPos": {"h": 7, "w": 24, "x": 0, "y": 0},
                    "id": 2,
                    "options": {
                        "legend": {
                            "calcs": [],
                            "displayMode": "list",
                            "placement": "bottom",
                            "showLegend": "true",
                        },
                        "tooltip": {"mode": "single", "sort": "none"},
                    },
                    "targets": [
                        {
                            "columns": [],
                            "datasource": {
                                "type": "yesoreyeram-infinity-datasource",
                                "uid": "P3E0B65AA66943F6C",
                            },
                            "filters": [],
                            "format": "table",
                            "global_query_id": "",
                            "refId": "A",
                            "root_selector": "",
                            "source": "url",
                            "type": "json",
                            "url": f"{host}:{port}/archive",
                            "url_options": {"data": "", "method": "GET"},
                        }
                    ],
                    "title": "Task Result Status",
                    "transformations": [
                        {
                            "id": "convertFieldType",
                            "options": {
                                "conversions": [
                                    {
                                        "dateFormat": "YYYY-MM-DD HH:mm:ss",
                                        "destinationType": "time",
                                        "targetField": "timestamp",
                                    },
                                    {
                                        "destinationType": "boolean",
                                        "targetField": "result",
                                    },
                                ],
                                "fields": {},
                            },
                        }
                    ],
                    "type": "timeseries",
                },
                {
                    "datasource": {
                        "type": "yesoreyeram-infinity-datasource",
                        "uid": "P3E0B65AA66943F6C",
                    },
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "custom": {
                                "align": "auto",
                                "cellOptions": {"type": "auto"},
                                "inspect": "false",
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "red", "value": 80},
                                ],
                            },
                        },
                        "overrides": [],
                    },
                    "gridPos": {"h": 20, "w": 24, "x": 0, "y": 7},
                    "id": 1,
                    "options": {
                        "cellHeight": "sm",
                        "footer": {
                            "countRows": "false",
                            "fields": "",
                            "reducer": ["sum"],
                            "show": "false",
                        },
                        "showHeader": "true",
                    },
                    "pluginVersion": "10.4.0",
                    "targets": [
                        {
                            "columns": [],
                            "datasource": {
                                "type": "yesoreyeram-infinity-datasource",
                                "uid": "P3E0B65AA66943F6C",
                            },
                            "filters": [],
                            "format": "table",
                            "global_query_id": "",
                            "refId": "A",
                            "root_selector": "",
                            "source": "url",
                            "type": "json",
                            "url": f"{host}:{port}/archive",
                            "url_options": {"data": "", "method": "GET"},
                        }
                    ],
                    "title": "Panel Title",
                    "transformations": [
                        {
                            "id": "convertFieldType",
                            "options": {
                                "conversions": [
                                    {
                                        "dateFormat": "YYYY-MM-DD HH:mm:ss",
                                        "destinationType": "time",
                                        "targetField": "timestamp",
                                    },
                                    {
                                        "destinationType": "boolean",
                                        "targetField": "result",
                                    },
                                ],
                                "fields": {},
                            },
                        }
                    ],
                    "type": "table",
                },
            ],
            "schemaVersion": 39,
            "tags": [],
            "templating": {"list": []},
            "time": {"from": "now-6h", "to": "now"},
            "timepicker": {},
            "timezone": "browser",
            "title": "Task Table",
            "uid": "cdfqcy57u0gzkd",
            "version": 4,
            "weekStart": "",
        }

    def write_provisioning_files(
        self, datasources_dir: Path = None, dashboards_dir: Path = None
    ):
        # Ensure directories exist
        datasources_dir = datasources_dir or GF_DATASOURCES_DIR
        dashboards_dir = dashboards_dir or GF_DASHBOARDS_DIR

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

        # Log or handle the fact that files are written
        logger.info(f"Datasource files written: {data_source_path}")
        logger.info(f"Dashboard files written: {dashboard_path}")

    def setup_routes(self):
        @self.app.get("/jobs")
        async def get_jobs():
            # Fetch and format jobs data
            jobs_data = (
                self.timekeeper.get_jobs()
            )  # This should return a dict or list of jobs
            formatted_jobs = [
                {
                    "id": job_id,
                    "timestamp": datetime.strptime(
                        job["created"], "%Y-%m-%dT%H:%M:%S.%f"
                    ).isoformat(),
                    "task": job["task"],
                    "result": job["result"],
                    "kwargs": job["kwargs"],
                    "schedule_time": datetime.strptime(
                        job["schedule_time"], "%Y-%m-%dT%H:%M:%S.%f"
                    ),
                }
                for job_id, job in jobs_data.items()
            ]
            return formatted_jobs

        @self.app.get("/archive")
        async def get_archive():
            # Fetch and format archive data similarly
            archive_data = (
                self.timekeeper.get_archive()
            )  # This should return a dict or list of archived jobs
            formatted_archive = [
                {
                    "id": archive_id,
                    "timestamp": datetime.strptime(
                        archive["created"], "%Y-%m-%dT%H:%M:%S.%f"
                    ).isoformat(),
                    "task": archive["task"],
                    "result": archive["result"],
                    "kwargs": archive["kwargs"],
                    "schedule_time": datetime.strptime(
                        archive["schedule_time"], "%Y-%m-%dT%H:%M:%S.%f"
                    ),
                }
                for archive_id, archive in archive_data.items()
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
