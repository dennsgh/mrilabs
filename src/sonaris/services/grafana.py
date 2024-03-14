
from sonaris.utils.container import start_container, stop_container, remove_container, client,network
from typing import NoReturn, Optional
import hashlib
from docker.models.containers import Container
from docker import DockerClient
from sonaris.defaults import APP_NAME,SONARIS_NETWORK_NAME, GF_SECURITY_ADMIN_PASSWORD, GF_PORT, GF_DASHBOARDS_DIR,GF_DATASOURCES_DIR
from sonaris.utils.log import get_logger
from sonaris.services.service import Service
from pathlib import Path
from docker.models.networks import Network 
logger= get_logger()


class GrafanaContainerService(Service):
    def __init__(self, client: DockerClient = None ,port:int = None,datasources_dir:Path = None, dashboards_dir:Path = None,network_name: str = SONARIS_NETWORK_NAME) -> None:
        self._client :DockerClient = client
        self._network_name :str= network_name
        self.ensure_docker_client()
        self._network :Network = None
        self.ensure_docker_network()
        self.port :int= port or GF_PORT
        self.container_label = self.get_container_label()
        self.datasources_dir :Path = datasources_dir or GF_DATASOURCES_DIR
        self.dashboards_dir :Path= dashboards_dir or GF_DASHBOARDS_DIR
    def ensure_docker_client(self):
        """Ensure the Docker client is available and connected."""
        if self._client is None:
            try:
                self._client = DockerClient.from_env()
                logger.info(f"Docker client obtained: {self._client}")
                self._client.ping()  # Check connection to Docker
            except Exception as e:
                logger.error(f"Failed to obtain Docker client: {e}")
                self._client = None

    def ensure_docker_network(self):
        """Ensure the Docker network is available."""
        if self._network is None and self._client is not None:
            try:
                self._network = self._client.networks.get(self._network_name)
                logger.info(f"Found existing network: {self._network_name}")
            except Exception as e:
                try:
                    self._network = self._client.networks.create(self._network_name, driver="bridge", check_duplicate=True)
                    logger.info(f"Created new network: {self._network_name}")
                except Exception as e:
                    logger.error(f"Failed to create or retrieve network: {e}")
                    self._network = None

    @property
    def client(self):
        """Property to get the Docker client, fetching it if necessary."""
        if self._client is None:
            self.ensure_docker_client()
        return self._client

    @property
    def network(self):
        """Property to get the Docker network, creating or fetching it if necessary."""
        if self._network is None:
            self.ensure_docker_network()
        return self._network
    def _generate_hash_(self) -> str:
        """Static hash for container labeling."""
        return hashlib.sha256(str(APP_NAME).encode()).hexdigest()[:10]

    def find_grafana_container(self) -> Optional[Container]:
        """
        Find the Grafana container by label.
        :return: The Grafana Container if found, None otherwise.
        """
        if self.client is None:
            return None
        containers = self.client.containers.list(all=True, filters={"label": f"{APP_NAME.lower()}={self.container_label}"})
        return containers[0] if containers else None
    
    def get_container_label(self) -> str:
        return f"{APP_NAME.lower()}_{self._generate_hash_()}"
    
    def is_docker_client_online(self) -> bool:
        if self.client is None:
            logger.error("Docker client is not found. start Docker and restart the application.")
            return False
        return 
    
    def create_grafana_container(self, image: str = "grafana/grafana", network_name: str = "sonaris_network") -> Optional[str]:
        """Create and start a Grafana container on a custom Docker network."""
        if self.client is None:
            logger.error("Docker client is unavailable. Cannot start Grafana service.")
            return None
        try:
            container_label = self.get_container_label()
            container: Container = self.client.containers.run(
                image,
                ports={'3000/tcp': self.port},  # Map Grafana's default port to the specified port on the host
                environment={
                    'GF_SECURITY_ADMIN_PASSWORD': f'{GF_SECURITY_ADMIN_PASSWORD}',
                },
                labels={f"{APP_NAME.lower()}": container_label},
                detach=True
            )
            if self.network:
                self.network.connect(container)
            logger.info(f"Grafana container {container_label} created and started on custom network '{network_name}'. Accessible on http://localhost:{self.port}.")
            return container.id
        except Exception as e:
            logger.error(f"Failed to create Grafana container: {e}")
            return None
    def start(self) -> None:
        """
        Start the Grafana service by finding or creating the necessary container.
        """
        if self.client is None:
            logger.error("Docker client is unavailable. Cannot start Grafana service.")
            return

        container = self.find_grafana_container()
        if container is None:
            logger.info("Grafana container not found, creating a new one...")
            self.create_grafana_container()
        else:
            logger.info(f"Found existing Grafana container with container id: {container.id}")
            if container.status != 'running':
                container.start()
                logger.info("Grafana container started.")
            else:
                logger.info("Grafana container is already running.")

    def stop(self) -> None:
        """
        Stop the Grafana service.
        """
        if self.client is None:
            logger.error("Docker client is unavailable. Cannot stop Grafana service.")
            return

        container = self.find_grafana_container()
        if container and container.status == 'running':
            container.stop()
            logger.info("Grafana container stopped.")
        else:
            logger.info("No running Grafana container found to stop.")
            
    def stop_container(self, container_id: str) -> NoReturn:
        stop_container(container_id)
        
    def start_container(self, container_id: str) -> NoReturn:
        start_container(container_id)

    def recreate_grafana_container_with_volumes(self):
        if self.client is None:
            logger.error("Docker client is unavailable. Cannot recreate Grafana service.")
            return 
        existing_container = self.find_grafana_container()
        if existing_container:
            existing_container.stop()
            existing_container.remove()
        self.create_grafana_container()