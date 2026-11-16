"""Strict priority normalization for the concurrent execution benchmark."""


def normalize_priority(value) -> str:
    """Return an accepted canonical priority, rejecting every other input."""
    if type(value) is not str or value not in ("LOW", "MEDIUM", "HIGH"):
        raise ValueError("priority must be LOW, MEDIUM, or HIGH")
    return value
