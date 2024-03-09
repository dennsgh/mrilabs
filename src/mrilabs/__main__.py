import os
import signal

import click
from dotenv import load_dotenv

# Assuming create_app is defined elsewhere in your application
from mrilabs.app import create_app, signal_handler
from mrilabs.utils.logging import get_logger

# Configure logger
logger = get_logger()


def ensure_env_variables():
    """
    Ensure key environment variables are set, using default values if necessary.
    """
    # Load the environment variables from .env file
    load_dotenv()

    # Define the key environment variables to check and their default values
    key_env_vars = ["WORKINGDIR", "CONFIG", "DATA", "LOGS", "PYTHONPATH", "ASSETS"]

    # Set environment variables to "" if they are not already set
    for var in key_env_vars:
        if not os.getenv(var):
            os.environ[var] = ""


@click.group()
def cli():
    """
    MRI Labs Command Line Interface.
    """
    pass


def run_application(hardware_mock):
    """Function to initialize and run the MRI Labs application."""
    args_dict = {"hardware_mock": hardware_mock}
    logger.info(args_dict)
    app, window = create_app(args_dict)
    window.show()
    app.exec()


@cli.command()
@click.option(
    "--hardware-mock", "-hm", is_flag=True, help="Run the app in hardware mock mode."
)
def run(hardware_mock):
    """Run the MRI Labs application."""
    signal.signal(signal.SIGINT, signal_handler)
    try:
        ensure_env_variables()
        logger.info("Running application...")
        run_application(hardware_mock)
    except KeyboardInterrupt:
        logger.info("Exit signal detected.")


if __name__ == "__main__":
    cli()
