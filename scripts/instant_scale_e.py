"""Epoch normalization for the disposable Instant scale benchmark."""


def normalize_epoch(value) -> int:
    """Return exact integers 0 through 9; reject everything else."""
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError("epoch must be an integer from 0 through 9")
    return value
