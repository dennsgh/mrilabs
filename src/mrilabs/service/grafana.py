import json
import requests


class GrafanaService:

    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def create_dashboard(self, dashboard_title, dashboard_data):
        """
        Creates a new dashboard in Grafana.

        Args:
            dashboard_title (str): The title of the dashboard.
            dashboard_data (dict): A dictionary containing the dashboard JSON data.

        Returns:
            dict: The response from the Grafana API.
        """

        url = f"{self.url}/api/dashboards"
        response = requests.post(url,
                                 headers=self.headers,
                                 json=dashboard_data)
        response.raise_for_status(
        )  # Raise an exception for non-2xx status codes
        return response.json()


# Example usage
grafana_url = "http://localhost:3000"  # Replace with your Grafana URL
grafana_api_key = "YOUR_GRAFANA_API_KEY"  # Replace with your API key

dashboard_data = {
    "title":
    "My Barebones Dashboard",
    "rows": [{
        "title":
        "Row 1",
        "panels": [{
            "title": "Panel 1",
            "type": "graph",
            # Add your panel-specific data and options here
        }]
    }]
}

grafana_service = GrafanaService(grafana_url, grafana_api_key)
response = grafana_service.create_dashboard(dashboard_data["title"],
                                            dashboard_data)
print(f"Dashboard created successfully! ID: {response['id']}")
