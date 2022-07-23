"""Abstract Unit of Work."""
from typing import ContextManager, Protocol, Type

from ..repository import Repository


class UnitOfWork(ContextManager, Protocol):
    """An abstract Unit of Work."""

    batches: Repository

    def __exit__(
        self, exc_type: Type[BaseException] | None, _: object, _2: object
    ) -> None:
        self.rollback()

    def commit(self) -> None:
        """Commit the work done to the repository."""

    def rollback(self) -> None:
        """Undo everything."""
