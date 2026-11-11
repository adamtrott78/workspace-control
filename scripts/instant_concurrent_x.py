"""Strict slot normalization for the disposable concurrency benchmark."""


def normalize_slot(value) -> int:
    """Accept only built-in integers from 1 through 8."""
    if type(value) is not int or not 1 <= value <= 8:
        raise ValueError("slot must be an exact int in range 1..8")
    return value
