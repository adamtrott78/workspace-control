"""Strict attempt normalization for lease recovery benchmark."""


def normalize_attempt(value) -> int:
    """Accept only exact integers from zero through three."""
    if type(value) is not int or not 0 <= value <= 3:
        raise ValueError("attempt must be an exact int in [0, 3]")
    return value
