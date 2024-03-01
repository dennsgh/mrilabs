import inspect
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from header import ErrorLevel


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


def validate_task_parameters(
    task_function, parameters: Dict[str, Any]
) -> Tuple[bool, List[str], List[str]]:
    sig = inspect.signature(task_function)
    errors = []
    warnings = []

    for name, param in sig.parameters.items():
        expected_type = param.annotation
        provided_value = parameters.get(name, inspect.Parameter.empty)

        # Check for missing parameters
        if provided_value is inspect.Parameter.empty:
            if param.default is inspect.Parameter.empty:
                errors.append(f"Missing required param: {name}.")
            else:
                warnings.append(f"Missing optional param: {name}, using default value.")
        elif (
            not is_type_compatible(expected_type, provided_value)
            and expected_type is not inspect.Parameter.empty
        ):
            errors.append(
                f"Type mismatch: {name} (got {type(provided_value).__name__}, expected {expected_type.__name__})"
            )

    for name in parameters:
        if name not in sig.parameters:
            errors.append(f"Extra param provided: {name}.")

    is_valid = not errors
    return is_valid, errors, warnings


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


def get_function_to_validate(
    name: str, task_functions: Dict[str, Callable], task_enum: Optional[Enum]
) -> Optional[Callable]:
    """
    Attempt to match the name to a function in task_functions directly or via an Enum.

    Args:
        name: The name of the task to match.
        task_functions: A dictionary mapping task names to their corresponding functions.
        task_enum: An optional Enum class that maps task names or values to function keys in task_functions.

    Returns:
        The matched function if found, None otherwise.
    """
    # Try to get the function directly by name
    name = name.upper()
    function_to_validate = task_functions.get(name.upper())

    # If not found and an Enum is provided, try matching against Enum names or values
    if not function_to_validate and task_enum:
        for enum_member in task_enum:
            if (
                str(enum_member.name).upper() == name
                or str(enum_member.value).upper() == name
            ):
                return task_functions.get(enum_member.value)

    return function_to_validate


def validate_configuration(
    config: Dict[str, Any], task_functions: Dict[str, Callable], task_enum: Enum = None
) -> List[Tuple[str, bool, str, ErrorLevel]]:
    results = []
    for index, step in enumerate(
        config.get("experiment", {}).get("steps", []), start=1
    ):
        name = step.get("task").upper()
        function_to_validate = get_function_to_validate(name, task_functions, task_enum)

        if function_to_validate:
            is_valid, errors, warnings = validate_task_parameters(
                function_to_validate, step.get("parameters", {})
            )
            error_level = ErrorLevel.INFO if is_valid else ErrorLevel.BAD_CONFIG
            message = "Validation issues: " + "; ".join(errors + warnings)
            results.append((f"Step {index}: {name}", is_valid, message, error_level))
        else:
            results.append(
                (
                    f"Step {index}: {name}",
                    False,
                    "Task function not found.",
                    ErrorLevel.BAD_CONFIG,
                )
            )

    for result in results:
        print(result)
    return results


def validate_task(
    name: str, task_functions: Dict[str, Callable], task_enum: Enum = None
) -> List[Tuple[str, bool, str]]:
    name = str(name).upper()

    # Use the refactored function to get the function to validate
    function_to_validate = get_function_to_validate(name, task_functions, task_enum)

    # Proceed with validation if a matching function is found
    if function_to_validate:
        return True
    return False
