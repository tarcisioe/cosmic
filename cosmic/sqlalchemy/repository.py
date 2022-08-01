"""A Repository implementation using SQLAlchemy."""
from dataclasses import dataclass

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from ..domain.product import Product


@dataclass
class SQLAlchemyProductRepository:
    """A SQLAlchemy-based Repository."""

    session: Session

    def add(self, product: Product) -> None:
        """Add a batch to the repository."""
        self.session.add(product)

    def get(self, sku: str) -> Product | None:
        """Add a batch to the repository."""
        try:
            return self.session.query(Product).filter_by(sku=sku).one()
        except NoResultFound:
            return None
