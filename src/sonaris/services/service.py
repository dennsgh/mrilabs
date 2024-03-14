from abc import ABC, abstractmethod
from typing import NoReturn
from uvicorn.server import Server,Config
import contextlib
import time
from fastapi import FastAPI
import threading
class Service(ABC):
    def __init__(self):
        pass
    @abstractmethod
    def start(self) -> NoReturn:
        """
        Start the service, creating or finding necessary resources.
        """
        raise NotImplementedError
    
    @abstractmethod
    def stop(self) -> NoReturn:
        """
        Stop the service and clean up resources if necessary.
        """
        raise NotImplementedError

class MultithreadedServer:
    def __init__(self, app: FastAPI, host: str = "0.0.0.0", port: int = 8000, log_level: str = "info"):
        self.config = Config(app=app, host=host, port=port, log_level=log_level)
        self.server = Server(config=self.config)
        self.thread = threading.Thread(target=self.server.run, args=(), daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        # Uvicorn doesn't provide a direct way to stop the server from another thread, but setting `should_exit` helps in stopping the loop.
        self.server.should_exit = True
        self.thread.join()