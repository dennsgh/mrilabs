import signal

from dotenv import load_dotenv

from app import run_application, signal_handler
from utils.logging import get_logger

logger = get_logger()
if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)
    try:
        load_dotenv()
        logger.info("Running application...")
        run_application()
    except KeyboardInterrupt:
        logger.info("Exit signal detected.")
