import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Global logger variable
logger = None


def load_json_with_backup(path: Path):
    """
    Attempts to load a JSON file from the given path. If the file is corrupt,
    it creates a numbered backup and returns an empty dictionary.
    """
    if path.exists():
        try:
            with open(path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"Corrupt JSON file detected: {e}. Creating a numbered backup.")
            backup_path = create_numbered_backup(path)
            path.rename(backup_path)
        except Exception as e:
            print(f"Unexpected error loading JSON file: {e}.")
    return {}


def save_json(data, path: Path):
    """
    Saves the given data as a JSON file to the specified path.
    """
    try:
        with open(path, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Unexpected error loading JSON file: {e}.")


def create_numbered_backup(original_path: Path):
    """
    Creates a numbered backup for the given path, ensuring no existing backup is overwritten.
    """
    backup_base = original_path.with_suffix(".bak")
    counter = 1
    new_backup = Path(f"{backup_base}_{counter}")
    while new_backup.exists():
        counter += 1
        new_backup = Path(f"{backup_base}_{counter}")
    return new_backup


def init_logging():
    global logger
    if logger is None:
        logger_name = os.getenv("LOGGER_NAME", "logs")
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        logs_path = Path(os.getenv("LOGS", Path.cwd() / "logs"))
        if not logs_path.is_dir():
            logs_path.mkdir(parents=True, exist_ok=True)
        log_file_path = logs_path / f"{logger_name}.log"

        # Handler for writing logs to a file
        file_handler = RotatingFileHandler(
            filename=str(log_file_path), maxBytes=10000000, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)

        # Handler for printing logs to the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Adjusted formatter to include module names
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Adding both handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)


def get_logger(module_name=None):
    if logger is None:
        init_logging()
    if module_name:
        return logging.getLogger(f"{os.getenv('LOGGER_NAME', 'logs')}.{module_name}")
    return logger
