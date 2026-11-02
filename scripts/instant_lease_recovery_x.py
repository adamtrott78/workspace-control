"""Bounded attempt normalization."""


def normalize_attempt(value) -> int:
    """Return an exact integer attempt in [0, 3], otherwise raise ValueError."""
    if type(value) is not int or not 0 <= value <= 3:
        raise ValueError("attempt must be an exact int between 0 and 3")
    return value
