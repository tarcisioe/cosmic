"""Customer order descriptions."""
from dataclasses import dataclass
from typing import NewType

SKU = NewType("SKU", str)
OrderReference = NewType("OrderReference", str)


@dataclass(frozen=True, slots=True)
class OrderLine:
    """One line of an Order, with a product's SKU and a quantity."""

    order: OrderReference
    sku: SKU
    quantity: int


@dataclass
class Order:
    """A customer's order, identified by a reference and containing order lines."""

    reference: OrderReference
    lines: list[OrderLine]
