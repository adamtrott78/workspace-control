"""Mode normalization for the disposable Instant scale benchmark."""


def normalize_mode(value) -> str:
    """Return an exact supported mode or raise ValueError."""
    if type(value) is not str or value not in ("READ", "WRITE"):
        raise ValueError("mode must be READ or WRITE")
    return value
