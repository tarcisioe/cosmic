"""The service layer."""
from typing import Iterable

from ..domain.batch import Batch, BatchCandidate, BatchReference
from ..domain.order import SKU, OrderLine
from ..domain.product import Product
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
        product = uow.products.get(line.sku)

        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")

        batchref = product.allocate(line)
        uow.commit()

        if batchref is None:
            raise OutOfStock(f"Out of stock for sku {line.sku}")

    return batchref


def add_batch(candidate: BatchCandidate, uow: UnitOfWork) -> None:
    """Add a new batch to the repository."""
    with uow:
        product = uow.products.get(candidate.sku)

        new_batch = Batch(
            BatchReference(candidate.reference),
            SKU(candidate.sku),
            candidate.quantity,
            candidate.eta,
        )

        if product is None:
            product = Product(new_batch.sku, [])
            uow.products.add(product)

        product.batches.append(new_batch)
        uow.commit()
