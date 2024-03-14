import os
import platform
import signal

if platform.system() == "Windows":
    import ctypes

    myappid = "sonaris.sonaris.dummy.string"  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
import click
from dotenv import load_dotenv

# Assuming create_app is defined elsewhere in your application
from sonaris.app import create_app, signal_handler
from sonaris.utils.log import get_logger

# Configure logger
logger = get_logger()


def ensure_env_variables():
    """
    Ensure key environment variables are set, using default values if necessary.
    """
    # Load the environment variables from .env file
    load_dotenv()

    # Define the key environment variables to check and their default values
    key_env_vars = ["WORKINGDIR", "DATA", "PYTHONPATH", "ASSETS"]

    # Set environment variables to "" if they are not already set
    for var in key_env_vars:
        if not os.getenv(var):
            os.environ[var] = ""
            continue
        print(f"{var}: {os.getenv(var)}")

@click.group()
def cli():
    """
    Sonaris Command Line Interface.
    """
    pass


def run_application(hardware_mock,grafana):
    """Function to initialize and run the Sonaris application."""
    args_dict = {"hardware_mock": hardware_mock,
                 "grafana": grafana}
    logger.info(args_dict)
    app, window = create_app(args_dict)
    window.show()
    app.exec()



@cli.command()
@click.option("--hardware-mock", "-hm", is_flag=True, help="Run the app in hardware mock mode.")
@click.option("--grafana", is_flag=True, help="Start Grafana container alongside the application. Requires Docker.")
def run(hardware_mock, grafana):
    """Run the Sonaris application."""
    signal.signal(signal.SIGINT, signal_handler)
    try:
        ensure_env_variables()
        logger.info("Running application...")
        run_application(hardware_mock, grafana)
    except KeyboardInterrupt:
        logger.info("Exit signal detected.")

if __name__ == "__main__":
    cli()