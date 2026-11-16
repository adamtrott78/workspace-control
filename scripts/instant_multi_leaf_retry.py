"""Bounded retry-budget utilities for the disposable benchmark."""


def normalize_budget(value):
    """Validate an exact integer budget in the inclusive range zero to four."""
    if type(value) is not int or not 0 <= value <= 4:
        raise ValueError("budget must be an exact integer between 0 and 4")
    return value


def next_budget(current, outcome):
    """Compute the next bounded budget for an exact outcome token."""
    current = normalize_budget(current)
    if type(outcome) is not str:
        raise ValueError("invalid outcome")
    if outcome == "PASS":
        return 0
    if outcome == "RETRYABLE_FAILURE":
        return min(current + 1, 4)
    if outcome == "TERMINAL_FAILURE":
        return 4
    raise ValueError("invalid outcome")
