import functools


def parameter_annotations(**annotations):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        if annotations:
            wrapper.parameter_annotations = annotations
        return wrapper

    return decorator


def parameter_constraints(**constraints):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Attach only if constraints are provided
        if constraints:
            wrapper.parameter_constraints = constraints
        return wrapper

    return decorator
