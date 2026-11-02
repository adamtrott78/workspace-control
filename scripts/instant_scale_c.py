"""Priority normalization for the disposable Instant scale benchmark."""


def normalize_priority(value) -> str:
    """Return an exact supported priority, rejecting all other values."""
    if type(value) is not str or value not in ("LOW", "MEDIUM", "HIGH"):
        raise ValueError("priority must be LOW, MEDIUM, or HIGH")
    return value
