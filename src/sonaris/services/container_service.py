import hashlib
from pathlib import Path
from typing import Optional

from docker import DockerClient
from docker.models.containers import Container
from docker.models.networks import Network

from sonaris.services.service import Service
from sonaris.utils.log import get_logger

logger = get_logger()


class ContainerService(Service):
    def __init__(
        self,
        client: DockerClient = None,
        network_name: str = None,
        service_name: str = None,
        image: str = None,
        container_label: str = None,
    ):
        self._client: DockerClient = client
        self._network_name: str = network_name
        self.service_name: str = service_name
        self.image: str = image
        self._container_label: str = container_label or self._generate_hash_()
        self._network: Network = None
        self.ensure_docker_client()
        self.ensure_docker_network()

    def ensure_docker_client(self):
        if self._client is None:
            try:
                self._client = DockerClient.from_env()
                logger.info(f"Docker client obtained: {self._client}")
                self._client.ping()
            except Exception as e:
                logger.error(f"Failed to obtain Docker client: {e}")
                self._client = None

    def ensure_docker_network(self):
        if self._network is None and self._client is not None:
            try:
                self._network = self._client.networks.get(self._network_name)
                logger.info(f"Found existing network: {self._network_name}")
            except Exception as e:
                try:
                    self._network = self._client.networks.create(
                        self._network_name, driver="bridge", check_duplicate=True
                    )
                    logger.info(f"Created new network: {self._network_name}")
                except Exception as e:
                    logger.error(f"Failed to create or retrieve network: {e}")
                    self._network = None

    def _generate_hash_(self) -> str:
        class_name = (self.__class__.__name__).encode("utf-8")
        return hashlib.sha256(class_name).hexdigest()[:10]

    @property
    def client(self):
        if self._client is None:
            self.ensure_docker_client()
        return self._client

    @property
    def network(self):
        if self._network is None:
            self.ensure_docker_network()
        return self._network

    def find_container(self) -> Optional[Container]:
        """
        Find the service container by label.
        :return: The service Container if found, None otherwise.
        """
        if self.client is None:
            return None
        containers = self.client.containers.list(
            all=True, filters={"label": f"{self.service_name}={self._container_label}"}
        )
        return containers[0] if containers else None

    def create_container(self, **kwargs) -> Optional[str]:
        """
        Create and start the service container.
        This method should be implemented by subclasses to include service-specific configurations.
        """
        raise NotImplementedError("Subclasses must implement create_container method.")

    def start(self) -> None:
        """
        Start the service by finding or creating the necessary container.
        """
        if self.client is None:
            logger.error(
                f"Docker client is unavailable. Cannot start {self.service_name} service."
            )
            return

        container = self.find_container()
        if container is None:
            logger.info(
                f"{self.service_name} container not found, creating a new one..."
            )
            self.create_container()
        else:
            logger.info(
                f"Found existing {self.service_name} container with id: {container.id}"
            )
            if container.status != "running":
                container.start()
                logger.info(f"{self.service_name} container started.")
            else:
                logger.info(f"{self.service_name} container is already running.")

    def stop(self) -> None:
        """
        Stop the service container.
        """
        if self.client is None:
            logger.error(
                f"Docker client is unavailable. Cannot stop {self.service_name} service."
            )
            return

        container = self.find_container()
        if container and container.status == "running":
            container.stop()
            logger.info(f"{self.service_name} container stopped.")
        else:
            logger.info(f"No running {self.service_name} container found to stop.")
