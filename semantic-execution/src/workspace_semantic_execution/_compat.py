"""Small runtime-compatibility shims for supported Python versions."""
from __future__ import annotations

try:
    from enum import StrEnum as StrEnum
except ImportError:  # Python 3.10
    from enum import Enum

    class StrEnum(str, Enum):
        """Python 3.10-compatible subset of enum.StrEnum."""

        def __str__(self) -> str:
            return str(self.value)
