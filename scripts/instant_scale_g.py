"""Batch-size normalization for the disposable multi-worker benchmark."""


def normalize_batch_size(value) -> int:
    """Accept exact integers from 1 through 16 inclusive."""
    if type(value) is not int or not 1 <= value <= 16:
        raise ValueError("batch size must be an exact int from 1 through 16")
    return value
