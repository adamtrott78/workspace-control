"""Validation helper for the disposable Instant scale benchmark."""


def normalize_retry_count(value) -> int:
    """Accept only exact integers from zero through three."""
    if type(value) is not int or not 0 <= value <= 3:
        raise ValueError("retry count must be an integer from 0 through 3")
    return value
