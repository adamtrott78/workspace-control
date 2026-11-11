"""Decision normalization for the disposable Instant scale benchmark."""


def normalize_decision(value) -> str:
    """Accept only the three exact uppercase decision tokens."""
    if type(value) is not str or value not in ("EXECUTE", "DECOMPOSE", "ESCALATE"):
        raise ValueError("decision must be EXECUTE, DECOMPOSE, or ESCALATE")
    return value
