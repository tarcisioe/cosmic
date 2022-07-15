"""Tests for domain functionality."""
from datetime import date

import pytest

from cosmic.domain.batch import (
    Batch,
    BatchReference,
    NotEnoughProductsOnBatch,
    allocate,
)
from cosmic.domain.order import SKU, OrderLine, OrderReference


def test_allocating_to_a_batch_reduces_the_available_quantity() -> None:
    """Allocating an order line on a batch should reduce the available quantity."""
    batch = Batch(
        BatchReference("batch001"), SKU("SMALL-TABLE"), 20, eta=date(1917, 10, 1)
    )
    order_line = OrderLine(OrderReference("order001"), SKU("SMALL-TABLE"), 2)

    batch.allocate(order_line)

    assert batch.available() == 18


def test_can_allocate_if_available_greater_than_required() -> None:
    """Batch.can_allocate should return True if the order fits the batch."""
    batch = Batch(
        BatchReference("batch001"), SKU("SMALL-TABLE"), 20, eta=date(1917, 10, 1)
    )
    order_line = OrderLine(OrderReference("order001"), SKU("SMALL-TABLE"), 18)

    assert batch.can_allocate(order_line)


def test_cannot_allocate_if_available_smaller_than_required() -> None:
    """Batch.can_allocate should return False if the order does not the batch."""
    batch = Batch(
        BatchReference("batch001"), SKU("SMALL-TABLE"), 20, eta=date(1917, 10, 1)
    )
    order_line = OrderLine(OrderReference("order001"), SKU("SMALL-TABLE"), 21)

    assert not batch.can_allocate(order_line)


def test_can_allocate_if_available_equal_to_required() -> None:
    """Batch.can_allocate should return True if the order fits the batch perfectly."""
    quantity = 20

    batch = Batch(
        BatchReference("batch001"), SKU("SMALL-TABLE"), quantity, eta=date(1917, 10, 1)
    )
    order_line = OrderLine(OrderReference("order001"), SKU("SMALL-TABLE"), quantity)

    assert batch.can_allocate(order_line)


def test_cannot_allocate_if_skus_do_not_match() -> None:
    """Batch.can_allocate should return False if the types of products don't match."""
    batch = Batch(
        BatchReference("batch001"), SKU("SMALL-TABLE"), 20, eta=date(1917, 10, 1)
    )
    order_line = OrderLine(OrderReference("order001"), SKU("RED-CHAIR"), 2)

    assert not batch.can_allocate(order_line)


def test_batch_allocate_raises_if_cannot_allocate():
    """Batch.allocate should fail if allocation is not possible."""
    batch = Batch(
        BatchReference("batch001"), SKU("SMALL-TABLE"), 20, eta=date(1917, 10, 1)
    )
    order_line = OrderLine(OrderReference("order001"), SKU("RED-CHAIR"), 25)

    with pytest.raises(NotEnoughProductsOnBatch):
        batch.allocate(order_line)


def test_can_only_deallocate_allocated_lines() -> None:
    """Batch.deallocate should only do something to allocated lines."""
    batch = Batch(
        BatchReference("batch001"), SKU("SMALL-TABLE"), 20, eta=date(1917, 10, 1)
    )
    order_line = OrderLine(OrderReference("order001"), SKU("SMALL-TABLE"), 2)

    batch.deallocate(order_line)

    assert batch.available() == 20


def test_allocation_is_idempotent() -> None:
    """Allocating the same order line twice to a batch should do nothing."""
    batch = Batch(
        BatchReference("batch001"), SKU("SMALL-TABLE"), 20, eta=date(1917, 10, 1)
    )
    order_line = OrderLine(OrderReference("order001"), SKU("SMALL-TABLE"), 2)

    batch.allocate(order_line)
    assert batch.available() == 18

    batch.allocate(order_line)
    assert batch.available() == 18


def test_prefers_warehouse_batches_to_shipments() -> None:
    """allocate() should prefer batches that already arrived on a warehouse."""
    in_stock_batch = Batch(
        BatchReference("in-stock-batch"), SKU("RETRO-CLOCK"), 100, eta=date(1917, 9, 30)
    )
    shipment_batch = Batch(
        BatchReference("shipment-batch"), SKU("RETRO-CLOCK"), 100, eta=date(1917, 10, 1)
    )
    line = OrderLine(OrderReference("oref"), SKU("RETRO-CLOCK"), 10)

    allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available() == 90
    assert shipment_batch.available() == 100


def test_allocate_prefers_earlier_batches() -> None:
    """allocate() should prefer batches that will arrive earlier."""
    earliest = Batch(
        BatchReference("speedy-batch"),
        SKU("MINIMALIST-SPOON"),
        100,
        eta=date(1917, 10, 1),
    )
    medium = Batch(
        BatchReference("normal-batch"),
        SKU("MINIMALIST-SPOON"),
        100,
        eta=date(1917, 10, 2),
    )
    latest = Batch(
        BatchReference("slow-batch"),
        SKU("MINIMALIST-SPOON"),
        100,
        eta=date(1917, 11, 2),
    )
    line = OrderLine(OrderReference("order1"), SKU("MINIMALIST-SPOON"), 10)

    allocate(line, [medium, earliest, latest])

    assert earliest.available() == 90
    assert medium.available() == 100
    assert latest.available() == 100


def test_allocate_returns_allocated_batch_ref():
    """allocate() should return the chosen batch reference."""
    in_stock_batch = Batch(
        BatchReference("in-stock-batch-ref"),
        SKU("HIGHBROW-POSTER"),
        100,
        eta=date(1917, 10, 1),
    )
    shipment_batch = Batch(
        BatchReference("shipment-batch-ref"),
        SKU("HIGHBROW-POSTER"),
        100,
        eta=date(1917, 10, 2),
    )
    line = OrderLine(OrderReference("oref"), SKU("HIGHBROW-POSTER"), 10)

    allocation = allocate(line, [in_stock_batch, shipment_batch])

    assert allocation == in_stock_batch.reference


def test_allocate_returns_none_if_cannot_allocate():
    """allocate() should return None if it cannot allocate."""
    batch = Batch(
        BatchReference("batch001"), SKU("SMALL-TABLE"), 20, eta=date(1917, 10, 1)
    )
    order_line = OrderLine(OrderReference("order001"), SKU("RED-CHAIR"), 2)

    assert allocate(order_line, [batch]) is None
