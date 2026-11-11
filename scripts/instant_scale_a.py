"""Worker-slot validation for the disposable scale benchmark."""


def normalize_worker_slot(value) -> int:
    """Return an integer worker slot in the inclusive range 1..4."""
    if type(value) is not int or not 1 <= value <= 4:
        raise ValueError("worker slot must be an exact int from 1 through 4")
    return value
