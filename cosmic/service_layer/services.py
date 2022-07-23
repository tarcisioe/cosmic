"""The service layer."""
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from ..domain import batch
from ..domain.batch import Batch, BatchReference
from ..domain.order import SKU, OrderLine
from .unit_of_work import UnitOfWork


class InvalidSku(Exception):
    """Signals that an invalid SKU was requested."""


class OutOfStock(Exception):
    """Signals that a requested SKU is out of stock."""


def is_valid_sku(sku, batches: Iterable[Batch]) -> bool:
    """Check that an SKU exists in the recorded batches."""
    return sku in {b.sku for b in batches}


def allocate(line: OrderLine, uow: UnitOfWork) -> str:
    """Validate input, perform the allocation and persist state."""
    with uow:
        batches = uow.batches.get_all()

        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f"Invalid sku {line.sku}")

        batchref = batch.allocate(line, batches)

        if batchref is None:
            raise OutOfStock(f"Out of stock for sku {line.sku}")

        uow.commit()

        return batchref


@dataclass
class BatchCandidate:
    """Candidate values for a Batch."""

    reference: str
    sku: str
    quantity: int
    eta: date


def add_batch(candidate: BatchCandidate, uow: UnitOfWork) -> None:
    """Add a new batch to the repository."""
    with uow:
        uow.batches.add(
            Batch(
                BatchReference(candidate.reference),
                SKU(candidate.sku),
                candidate.quantity,
                candidate.eta,
            )
        )

        uow.commit()
