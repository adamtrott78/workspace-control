"""Result normalization for the disposable multi-worker benchmark."""


def normalize_result(value) -> str:
    """Accept only exact uppercase result labels."""
    if type(value) is not str or value not in ("PASS", "FAIL", "PENDING"):
        raise ValueError("result must be PASS, FAIL, or PENDING")
    return value
