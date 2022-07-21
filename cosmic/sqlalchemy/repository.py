"""A Repository implementation using SQLAlchemy."""
from dataclasses import dataclass

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from ..domain.batch import Batch


@dataclass
class SQLAlchemyRepository:
    """A SQLAlchemy-based Repository."""

    session: Session

    def add(self, batch: Batch) -> None:
        """Add a batch to the repository."""
        self.session.add(batch)

    def get(self, batch_reference: str) -> Batch | None:
        """Add a batch to the repository."""
        try:
            return self.session.query(Batch).filter_by(reference=batch_reference).one()
        except NoResultFound:
            return None

    def get_all(self) -> list[Batch]:
        """Get all batches from the repository."""
        return self.session.query(Batch).all()
