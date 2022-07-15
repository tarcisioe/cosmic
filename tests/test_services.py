"""Tests for the service layer."""
from dataclasses import dataclass, field
from datetime import date

import pytest

from cosmic import services
from cosmic.domain.batch import Batch, BatchReference
from cosmic.domain.order import SKU, OrderLine, OrderReference


@dataclass
class FakeRepository:
    """Fake implementation of a repository."""

    _batches: dict[BatchReference, Batch] = field(default_factory=dict)

    def add(self, batch: Batch) -> None:
        """Add a batch to the repository."""
        self._batches[batch.reference] = batch

    def get(self, reference: BatchReference) -> Batch:
        """Get a batch from the repository by its reference."""
        return self._batches[reference]

    def get_all(self) -> list[Batch]:
        """Get all batches from the repository."""
        return list(self._batches.values())


class FakeSession:
    """Fake database session."""

    committed = False

    def commit(self) -> None:
        """Record a commit."""
        self.committed = True


def test_returns_allocation() -> None:
    """services.allocate should return the batch reference."""
    line = OrderLine(OrderReference("o1"), SKU("COMPLICATED-LAMP"), 10)
    batch = Batch(
        BatchReference("b1"), SKU("COMPLICATED-LAMP"), 100, eta=date(2010, 1, 1)
    )

    repo = FakeRepository({batch.reference: batch})

    result = services.allocate(line, repo, FakeSession())

    assert result == "b1"


def test_error_for_invalid_sku() -> None:
    """services.allocate should throw in case the SKU is invalid."""
    line = OrderLine(OrderReference("o1"), SKU("NONEXISTENTSKU"), 10)
    batch = Batch(BatchReference("b1"), SKU("AREALSKU"), 100, eta=date(2010, 1, 1))
    repo = FakeRepository({batch.reference: batch})

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate(line, repo, FakeSession())


def test_commits() -> None:
    """services.allocate should commit to the database."""
    line = OrderLine(OrderReference("o1"), SKU("OMINOUS-MIRROR"), 10)
    batch = Batch(
        BatchReference("b1"), SKU("OMINOUS-MIRROR"), 100, eta=date(2010, 1, 1)
    )
    repo = FakeRepository({batch.reference: batch})

    session = FakeSession()

    services.allocate(line, repo, session)

    assert session.committed is True
