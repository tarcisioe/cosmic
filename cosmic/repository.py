"""Repository abstractions."""
from typing import Protocol

from .domain.batch import Batch, BatchReference


class Repository(Protocol):
    """Protocol for our storage abstraction."""

    def add(self, batch: Batch) -> None:
        """Add a batch to the repository."""

    def get(self, batch_reference: BatchReference) -> Batch:
        """Get a Batch by its reference."""

    def get_all(self) -> list[Batch]:
        """Get all batches."""
