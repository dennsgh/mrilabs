import docker

from mrilabs.utils.logging import get_logger
logger = get_logger()
class GrafanaManager:

    def __init__(self):
        self.client = docker.from_env(
        )  # Use client instead of docker_client for consistency
        self.container = None

    def create_grafana(self):
        try:
            image = "grafana/grafana"
            config = {
                "Image": image,
                "Detach": True,
                "Ports": {
                    "3000/tcp": 3000
                },
                "Labels": {
                    "mrilabs_dashboard": "true"
                },
                "Name":
                "grafana_instance",  # Ensure name is defined before creation
            }
            self.container = self.client.create_container_from_config(config)
            logger.info("Grafana container started successfully!")
        except docker.client.errors.APIError as e: 
            logger.error(f"Docker API error: {e}")  
        except Exception as e:
            logger.error(f"Failed to start Grafana container: {e}")
    def start_grafana(self):
        self.client.start(self.container)

    def stop_grafana(self):
        if self.container:
            try:
                self.client.remove_container(self.container)
                logger.info("Grafana container stopped successfully!")
            except docker.client.errors.DockerException as e:  # Catch specific error if container not found
                logger.error(f"Failed to stop Grafana container: {e}")


if __name__ == "__main__":
    manager = GrafanaManager()

    # Start Grafana container
    manager.create_grafana()
    manager.start_grafana()

    # Do some operations with Grafana, e.g., provision dashboard
    import time
    
    time.sleep(10)
    # Stop Grafana container
    manager.stop_grafana()
