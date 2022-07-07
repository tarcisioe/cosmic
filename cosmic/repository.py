"""Repository abstractions."""
from typing import Protocol

from .batch import Batch


class Repository(Protocol):
    """Protocol for our storage abstraction."""

    def add(self, batch: Batch) -> None:
        """Add a batch to the repository."""
