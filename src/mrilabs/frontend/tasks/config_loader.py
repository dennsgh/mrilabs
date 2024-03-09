from typing import Any, Tuple

import yaml


class ConfigLoader:
    @staticmethod
    def load_config(config_path: str) -> Tuple[bool, str, Any]:
        try:
            with open(config_path, "r") as file:
                config = yaml.safe_load(file)
                if not config:
                    return False, "No configuration loaded", None
                return True, "Configuration loaded successfully", config
        except Exception as e:
            return False, f"Failed to load configuration: {str(e)}", None

    @staticmethod
    def save_config(config: dict, config_path: str) -> Tuple[bool, str]:
        try:
            with open(config_path, "w") as file:
                yaml.dump(config, file, sort_keys=False)
            return True, "Configuration saved successfully."
        except Exception as e:
            return False, f"Failed to save configuration: {str(e)}"