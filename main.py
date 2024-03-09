import argparse
import signal

from dotenv import load_dotenv

from mrilabs.app import run_application, signal_handler
from mrilabs.utils.logging import get_logger

logger = get_logger()
if __name__ == "__main__":
    # Not recommended anymore to run this way. (mrilabs/__main__.py controls the argument parsing using click)
    # Do python -m mrilabs run --hardware-mock to run the app in hardware mock mode instead ( or poetry run python -m mrilabs run --hardware-mock)
    # You can do packaged runs as well by doing 'pip install .'
    parser = argparse.ArgumentParser(description="Run the mrilabs application.")
    parser.add_argument(
        "--hardware-mock",
        action="store_true",
        help="Run the app in hardware mock mode.",
    )
    args = parser.parse_args()
    args_dict = vars(args)

    signal.signal(signal.SIGINT, signal_handler)
    try:
        load_dotenv()
        logger.info("Running application...")
        run_application(args_dict)
    except KeyboardInterrupt:
        logger.info("Exit signal detected.")
