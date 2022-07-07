"""A Repository implementation using SQLAlchemy."""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..batch import Batch, BatchReference


@dataclass
class SQLAlchemyRepository:
    """A SQLAlchemy-based Repository."""

    session: Session

    def add(self, batch: Batch) -> None:
        """Add a batch to the repository."""
        self.session.add(batch)

    def get(self, batch_reference: BatchReference) -> Batch:
        """Add a batch to the repository."""
        return self.session.query(Batch).filter_by(reference=batch_reference).one()
