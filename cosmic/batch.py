"""Operations on product batches."""
from dataclasses import dataclass, field
from datetime import date
from typing import NewType

from .order import SKU, OrderLine


class NotEnoughProductsOnBatch(Exception):
    """Happens when a batch doesn't have enough products to allocate an order line."""


BatchReference = NewType("BatchReference", str)


@dataclass(eq=False)
class Batch:
    """A product batch which is ordered from a manufacturer."""

    reference: BatchReference
    sku: SKU
    quantity: int
    eta: date
    _allocated: set[OrderLine] = field(init=False, default_factory=set)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Batch):
            return False
        return self.reference == other.reference

    def can_allocate(self, order_line: OrderLine) -> bool:
        """Check if a batch can allocate a given order line.

        Args:
            order_line: The order line to check if can be allocated.

        Returns:
            If the line can be allocated or not.
        """
        if self.sku != order_line.sku:
            return False

        return self.available() >= order_line.quantity

    def allocate(self, order_line: OrderLine) -> None:
        """Allocate an order line on a batch.

        Args:
            order_line: The order line to allocate.

        Raises:
            NotEnoughProductsOnBatch: if this batch does not contain enough products
                                      of the given type.
        """
        if not self.can_allocate(order_line):
            raise NotEnoughProductsOnBatch(
                f"Batch {self.reference} cannot allocate {order_line.quantity} "
                f"products of type {order_line.sku}. Available = {self.available()} "
                f"of type {self.sku}."
            )

        self._allocated.add(order_line)

    def deallocate(self, order_line: OrderLine) -> None:
        """Deallocate an order from a batch.

        Args:
            order_line: The order line to deallocate.
        """
        try:
            self._allocated.remove(order_line)
        except KeyError:
            pass

    def available(self) -> int:
        """Get the number of available products still remaining."""
        allocated_total = sum(line.quantity for line in self._allocated)
        return self.quantity - allocated_total


def allocate(order_line: OrderLine, batches: list[Batch]) -> None | BatchReference:
    """Allocate an order line in one of the available batches.

    Args:
        order_line: The order line to allocate.
        batches: The available batches to try to allocate the order on.

    Return:
        The reference of the chosen batch.
    """
    sorted_batches = sorted(batches, key=lambda b: b.eta)
    good_batch = next(
        (batch for batch in sorted_batches if batch.can_allocate(order_line)), None
    )

    if good_batch is None:
        return None

    good_batch.allocate(order_line)

    return good_batch.reference
