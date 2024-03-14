import docker
from docker.errors import APIError, NotFound
from sonaris.utils.log import get_logger
from docker.models.containers import Container
from typing import NoReturn
from sonaris.utils.log import get_logger
from sonaris.defaults import SONARIS_NETWORK_NAME

logger = get_logger()

#================================================================

client = None
network = None


if client is None:
    try:
        client = docker.DockerClient.from_env()
        logger.info(f"Docker client obtained: {client}")
        client.ping()  # Check connection to Docker
    except Exception as e:
        logger.error(f"Failed to obtain Docker client: {e}")
        client = None


if network is None and client is not None:
    try:
        network = client.networks.get(SONARIS_NETWORK_NAME)
        logger.info(f"Found existing network: {SONARIS_NETWORK_NAME}")
    except Exception as e:
        try:
            network = client.networks.create(SONARIS_NETWORK_NAME, driver="bridge", check_duplicate=True)
            logger.info(f"Created new network: {SONARIS_NETWORK_NAME}")
        except Exception as e:
            logger.error(f"Failed to create or retrieve network: {e}")
            network = None

    
#================================================================
    
    
def list_containers(all: bool = False) -> NoReturn:
    """
    List all containers.
    :param all: Whether to show all containers. Defaults to False (show running containers only).
    """
    for container in client.containers.list(all=all):
        logger.info(f"ID: {container.short_id}, Name: {container.name}, Status: {container.status}")

def start_container(container_id: str) -> NoReturn:
    """
    Start a container.
    :param container_id: ID or name of the container.
    """
    try:
        container: Container = client.containers.get(container_id)
        logger.info(f"Starting {container_id}.")
        container.start()
    except NotFound:
        logger.error(f"Container {container_id} not found.")
    except APIError as e:
        logger.error(f"API Error: {e.explanation}")

def stop_container(container_id: str) -> NoReturn:
    """
    Stop a container.
    :param container_id: ID or name of the container.
    """
    try:
        container: Container = client.containers.get(container_id)
        logger.info(f"Stopping {container_id}.")
        container.stop()
    except NotFound:
        logger.error(f"Container {container_id} not found.")
    except APIError as e:
        logger.error(f"API Error: {e.explanation}")

def remove_container(container_id: str) -> NoReturn:
    """
    Remove a container.
    :param container_id: ID or name of the container.
    """
    try:
        container: Container = client.containers.get(container_id)
        container.remove()
        logger.info(f"Container {container_id} removed.")
    except NotFound:
        logger.error(f"Container {container_id} not found.")
    except APIError as e:
        logger.error(f"API Error: {e.explanation}")