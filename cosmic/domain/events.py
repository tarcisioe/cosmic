"""Events that can happen in the system."""
from dataclasses import dataclass

from .batch import BatchCandidate
from .order import SKU, OrderCandidate


class Event:
    """Base class for all events."""


@dataclass
class OutOfStock(Event):
    """Signal that a given product is out of stock."""

    sku: SKU


@dataclass
class BatchCreated(Event):
    """Signal that a batch creation has been requested."""

    candidate: BatchCandidate


@dataclass
class AllocationRequired(Event):
    """Signal that an allocation has been required."""

    order_line: OrderCandidate
