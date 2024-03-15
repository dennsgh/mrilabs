import inspect
import traceback
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import ValidationError

from sonaris.defaults import EXPERIMENT_KEYWORD, ErrorLevel
from sonaris.tasks.model import Experiment, ExperimentWrapper, Task
from sonaris.utils.log import get_logger

logger = get_logger()


class Validator:
    def __init__(self, task_functions: Dict[str, Callable], task_enum: Optional[Enum]):
        self.task_functions = task_functions
        self.task_enum = task_enum

    def validate_config(
        self, experiment_wrapper: ExperimentWrapper
    ) -> Tuple[bool, List[str], ErrorLevel]:
        """Validate the overall configuration using Pydantic and custom logic."""
        try:
            # Assuming the experiment_wrapper is already a Pydantic model instance
            validation_results = self.validate_configuration(
                experiment_wrapper.experiment
            )
            if any(not result[1] for result in validation_results):
                return (
                    False,
                    [result[2] for result in validation_results],
                    ErrorLevel.BAD_CONFIG,
                )
            return True, [], ErrorLevel.INFO
        except ValidationError as e:
            return False, [str(e)], ErrorLevel.INVALID_YAML

    def validate_configuration(
        self, experiment: Experiment
    ) -> List[Tuple[str, bool, str, ErrorLevel]]:
        results = []
        for index, task in enumerate(experiment.steps, start=1):
            task_name = task.task.upper()
            try:
                task_function = self.get_function_to_validate(task)
            except Exception as e:
                logger.error(f"Task function {task_name} failed to load: {e}")

            if task_function:
                is_valid, errors, warnings = self.validate_task_parameters(
                    task_function, task
                )
                error_level = ErrorLevel.INFO if is_valid else ErrorLevel.BAD_CONFIG
                message = " " + "; ".join(errors + warnings)
                results.append(
                    (f"Step {index}: {task_name}", is_valid, message, error_level)
                )
            else:
                results.append(
                    (
                        f"Step {index}: {task_name}",
                        False,
                        "Task function not found.",
                        ErrorLevel.BAD_CONFIG,
                    )
                )
        return results

    def get_function_to_validate(self, task: Task) -> Optional[Callable]:
        """Match the name to a function in task_functions directly or via an Enum."""
        # Try direct lookup by task name (uppercased) in the task_functions dictionary
        function_to_validate = self.task_functions.get(task.task.upper())

        # If not found, try to match against Enum names or values
        if not function_to_validate and self.task_enum:
            for enum_member in self.task_enum:
                if (
                    enum_member.name.upper() == task.task.upper()
                    or enum_member.value.upper() == task.task.upper()
                ):
                    # If a match is found, attempt to get the corresponding function using enum_member's value
                    function_to_validate = self.task_functions.get(enum_member.value)
                    if function_to_validate:
                        return function_to_validate

        raise ValueError(f"{task.task} not found in task_functions dictionary")

    @staticmethod
    def is_in_enum(name: str, task_enum: Enum) -> Optional[Any]:
        """
        Finds and returns the corresponding Enum value for a given task name.

        Args:
            name: The name of the task to find in the Enum.
            task_enum: The Enum containing task names and values.

        Returns:
            True if part of enum.
        """
        name = name.upper()
        for enum_member in task_enum:
            if (
                str(enum_member.name).upper() == name
                or str(enum_member.value).upper() == name
            ):
                return True
        return False

    @staticmethod
    def get_task_enum_value(name: str, task_enum: Enum) -> Optional[Any]:
        """
        Finds and returns the corresponding Enum value for a given task name.

        Args:
            name: The name of the task to find in the Enum.
            task_enum: The Enum containing task names and values.

        Returns:
            The Enum value if a match is found, None otherwise.
        """
        name = name.upper()
        for enum_member in task_enum:
            if (
                str(enum_member.name).upper() == name
                or str(enum_member.value).upper() == name
            ):
                return enum_member.value
        return None

    @staticmethod
    def get_task_enum_name(name: str, task_enum: Enum) -> Optional[str]:
        """
        Finds and returns the Enum name for a given task name.

        Args:
            name: The name of the task to match.
            task_enum: The Enum class that maps task names to values.

        Returns:
            The Enum name if a match is found, None otherwise.
        """
        name = name.upper()
        for enum_member in task_enum:
            if (
                str(enum_member.name).upper() == name
                or str(enum_member.value).upper() == name
            ):
                return enum_member.name
        return None

    @staticmethod
    def is_type_compatible(expected_type, value) -> bool:
        """
        Checks if the provided value is compatible with the expected type,
        applying custom validation rules and handling unannotated parameters.
        """
        # Handle None values (for optional parameters)
        if value is None:
            return True

        # Default unannotated parameters to str
        if expected_type is inspect.Parameter.empty:
            expected_type = str

        # Custom handling for bool to ensure strict type matching
        if expected_type is bool:
            return isinstance(value, bool)

        # Allow int values for float parameters
        if expected_type is float and isinstance(value, int):
            return True

        # Treat everything as compatible with str
        if expected_type is str:
            return True

        # Check for direct type compatibility or instance of custom classes
        if isinstance(value, expected_type):
            return True

        # Handle complex types like lists, dicts by checking type only (not contents)
        if expected_type in [list, dict] and type(value) is expected_type:
            return True

        # Further validation for the contents of lists, dicts, or custom classes could be added here

        return False

    @staticmethod
    def get_default_value(param_name: str, expected_type: type) -> Any:
        # Example default value logic based on type or name
        default_values = {
            "frequency": 1.0,  # Default frequency in Hz
            "amplitude": 0.5,  # Default amplitude in V
        }
        if expected_type is int:
            return 0
        elif expected_type is float:
            return 0.0
        elif expected_type is bool:
            return False
        elif expected_type is str:
            return ""
        elif expected_type is list:
            return []
        elif expected_type is dict:
            return {}
        return default_values.get(param_name, None)

    @staticmethod
    def validate_task_parameters(
        task_function, task: Task
    ) -> Tuple[bool, List[str], List[str]]:
        sig = inspect.signature(task_function)
        errors = []
        warnings = []

        for name, param in sig.parameters.items():
            expected_type = param.annotation
            provided_value = task.parameters.get(name, inspect.Parameter.empty)

            # Check for missing parameters
            if provided_value is inspect.Parameter.empty:
                if param.default is inspect.Parameter.empty:
                    errors.append(f"Missing required param: {name}.")
                else:
                    warnings.append(
                        f"Missing optional param: {name}, using default value."
                    )
            elif (
                not Validator.is_type_compatible(expected_type, provided_value)
                and expected_type is not inspect.Parameter.empty
            ):
                errors.append(
                    f"Type mismatch: {name} (got {type(provided_value).__name__}, expected {expected_type.__name__})"
                )

        for name in task.parameters:
            if name not in sig.parameters:
                errors.append(f"Extra param provided: {name}.")

        is_valid = not errors
        return is_valid, errors, warnings

    def validate_task(task: Task) -> List[Tuple[str, bool, str]]:

        # Use the refactored function to get the function to validate
        try:
            function_to_validate = Validator.get_function_to_validate(task)
        except Exception as e:
            logger.error(f"Task function failed to load: {e}")
        if function_to_validate:
            return True
        return False
