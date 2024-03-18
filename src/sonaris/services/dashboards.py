# These JSON models are exports from the Grafana UI and are not meant to be hand modified
# Use the UI to generate these JSON models.

# The datasource is taken from the Grafana UI and its official documentation
DS_SONARIS_DATASOURCE = lambda host, port:{
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

TASK_DASHBOARD = """
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": {
          "type": "grafana",
          "uid": "-- Grafana --"
        },
        "enable": "true",
        "hide": "true",
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": 1,
  "links": [],
  "panels": [
    {
      "datasource": {
        "type": "yesoreyeram-infinity-datasource",
        "uid": "P3E0B65AA66943F6C"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "custom": {
            "align": "auto",
            "cellOptions": {
              "type": "auto"
            },
            "inspect": "false"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 7,
        "w": 24,
        "x": 0,
        "y": 0
      },
      "id": 5,
      "options": {
        "cellHeight": "sm",
        "footer": {
          "countRows": "false",
          "fields": "",
          "reducer": [
            "sum"
          ],
          "show": "false"
        },
        "showHeader": "true"
      },
      "pluginVersion": "10.4.0",
      "targets": [
        {
          "columns": [],
          "datasource": {
            "type": "yesoreyeram-infinity-datasource",
            "uid": "P3E0B65AA66943F6C"
          },
          "filters": [],
          "format": "table",
          "global_query_id": "archive",
          "refId": "A",
          "root_selector": "",
          "source": "url",
          "type": "json",
          "url": "http://host.docker.internal:5000/jobs",
          "url_options": {
            "data": "",
            "method": "GET"
          }
        }
      ],
      "title": "Scheduled Tasks",
      "transformations": [
        {
          "id": "extractFields",
          "options": {
            "format": "kvp",
            "keepTime": "false",
            "replace": "false",
            "source": "kwargs"
          }
        },
        {
          "id": "convertFieldType",
          "options": {
            "conversions": [
              {
                "dateFormat": "YYYY-MM-DD HH:mm:ss",
                "destinationType": "time",
                "targetField": "schedule_time"
              },
              {
                "dateFormat": "YYYY-MM-DD HH:mm:ss",
                "destinationType": "time",
                "targetField": "timestamp"
              },
              {
                "destinationType": "enum",
                "enumConfig": {
                  "text": [
                    "Pending"
                  ]
                },
                "targetField": "result"
              }
            ],
            "fields": {}
          }
        }
      ],
      "type": "table"
    },
    {
      "datasource": {
        "type": "yesoreyeram-infinity-datasource",
        "uid": "P3E0B65AA66943F6C"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
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
              "viz": "false"
            },
            "insertNulls": "false",
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "auto",
            "spanNulls": "false",
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 7,
        "w": 24,
        "x": 0,
        "y": 7
      },
      "id": 2,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": "true"
        },
        "tooltip": {
          "mode": "single",
          "sort": "none"
        }
      },
      "targets": [
        {
          "columns": [],
          "datasource": {
            "type": "yesoreyeram-infinity-datasource",
            "uid": "P3E0B65AA66943F6C"
          },
          "filters": [],
          "format": "table",
          "global_query_id": "",
          "refId": "A",
          "root_selector": "",
          "source": "url",
          "type": "json",
          "url": "http://host.docker.internal:5000/archive",
          "url_options": {
            "data": "",
            "method": "GET"
          }
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
                "targetField": "timestamp"
              },
              {
                "destinationType": "boolean",
                "targetField": "result"
              }
            ],
            "fields": {}
          }
        }
      ],
      "type": "timeseries"
    },
    {
      "datasource": {
        "type": "yesoreyeram-infinity-datasource",
        "uid": "P3E0B65AA66943F6C"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "custom": {
            "align": "auto",
            "cellOptions": {
              "type": "auto"
            },
            "inspect": "false"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 20,
        "w": 24,
        "x": 0,
        "y": 14
      },
      "id": 1,
      "options": {
        "cellHeight": "sm",
        "footer": {
          "countRows": "false",
          "fields": "",
          "reducer": [
            "sum"
          ],
          "show": "false"
        },
        "showHeader": "true"
      },
      "pluginVersion": "10.4.0",
      "targets": [
        {
          "columns": [],
          "datasource": {
            "type": "yesoreyeram-infinity-datasource",
            "uid": "P3E0B65AA66943F6C"
          },
          "filters": [],
          "format": "table",
          "global_query_id": "",
          "refId": "A",
          "root_selector": "",
          "source": "url",
          "type": "json",
          "url": "http://host.docker.internal:5000/archive",
          "url_options": {
            "data": "",
            "method": "GET"
          }
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
                "targetField": "timestamp"
              },
              {
                "destinationType": "boolean",
                "targetField": "result"
              }
            ],
            "fields": {}
          }
        }
      ],
      "type": "table"
    }
  ],
  "schemaVersion": 39,
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "browser",
  "title": "Task Table",
  "uid": "cdfqcy57u0gzkd",
  "version": 1,
  "weekStart": ""
}
"""
