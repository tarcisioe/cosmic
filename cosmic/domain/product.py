"""Aggregate for Batches."""
from collections import deque
from dataclasses import dataclass, field

from .batch import Batch, BatchReference, allocate
from .events import Event, OutOfStock
from .order import SKU, OrderLine


@dataclass
class Product:
    """Aggregate for Batches of products with the same SKU."""

    sku: SKU
    batches: list[Batch]
    version_number: int = 0
    _events: deque[Event] = field(init=False, default_factory=deque)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return False
        return self.sku == other.sku

    def __hash__(self) -> int:
        return hash(self.sku)

    def allocate(self, line: OrderLine) -> BatchReference | None:
        """Try to allocate an OrderLine on a batch from our collection."""
        result = allocate(line, self.batches)

        if result is None:
            self.events.append(OutOfStock(line.sku))
            return None

        self.version_number += 1
        return result

    @property
    def events(self) -> deque[Event]:
        """Get the events deque."""
        try:
            return self._events
        except AttributeError:
            self._events = deque()
            return self._events
