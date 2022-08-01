"""A Unit of Work implementation based on SQLAlchemy."""
from dataclasses import dataclass, field
from typing import Callable, Type

from sqlalchemy.orm import Session

from ..service_layer.unit_of_work import UnitOfWork
from .repository import SQLAlchemyProductRepository

SessionFactory = Callable[[], Session]


@dataclass
class SQLAlchemyUnitOfWork(UnitOfWork):
    """A Unit of Work implementation based on an SQLAlchemy session."""

    session_factory: SessionFactory
    session: Session = field(init=False)
    products: SQLAlchemyProductRepository = field(init=False)

    def __enter__(self) -> "SQLAlchemyUnitOfWork":
        self.session = self.session_factory()
        self.products = SQLAlchemyProductRepository(self.session)
        return self

    def __exit__(
        self, exc_type: Type[BaseException] | None, _: object, _2: object
    ) -> None:
        super().__exit__(exc_type, _, _2)
        self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
