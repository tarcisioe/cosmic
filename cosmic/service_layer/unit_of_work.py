"""Abstract Unit of Work."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Type

from ..messagebus import MessageBus
from ..repository import ProductRepository, TrackingProductRepository


class UnitOfWork(ABC):
    """An abstract Unit of Work."""

    products: ProductRepository

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(
        self, exc_type: Type[BaseException] | None, _: object, _2: object
    ) -> None:
        self.rollback()

    @abstractmethod
    def commit(self) -> None:
        """Commit the work done to the repository."""

    @abstractmethod
    def rollback(self) -> None:
        """Undo everything."""


@dataclass
class TrackingUnitOfWork(UnitOfWork):
    """A unit of work that uses a tracking repository."""

    wrapped: UnitOfWork
    messagebus: MessageBus
    products: TrackingProductRepository = field(init=False)

    def __enter__(self) -> "UnitOfWork":
        self.wrapped.__enter__()
        self.products = TrackingProductRepository(self.wrapped.products)
        return self

    def _publish(self) -> None:
        for product in self.products.seen:
            while product.events:
                event = product.events.popleft()
                self.messagebus.handle(event)

    def commit(self) -> None:
        self.wrapped.commit()
        self._publish()

    def rollback(self) -> None:
        self.wrapped.rollback()
