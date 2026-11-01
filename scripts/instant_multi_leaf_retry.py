"""Bounded retry-budget utilities for the disposable benchmark."""


def normalize_budget(value):
    """Validate an exact integer budget in the inclusive range zero to four."""
    if type(value) is not int or not 0 <= value <= 4:
        raise ValueError("budget must be an exact integer between 0 and 4")
    return value
