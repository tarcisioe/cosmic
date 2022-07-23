"""Tests for the service layer."""
from dataclasses import dataclass, field
from datetime import date

import pytest

from cosmic.domain.batch import Batch, BatchReference
from cosmic.domain.order import SKU, OrderLine, OrderReference
from cosmic.service_layer import services
from cosmic.service_layer.unit_of_work import UnitOfWork


@dataclass
class FakeRepository:
    """Fake implementation of a repository."""

    _batches: dict[BatchReference, Batch] = field(default_factory=dict)

    def add(self, batch: Batch) -> None:
        """Add a batch to the repository."""
        self._batches[batch.reference] = batch

    def get(self, reference: str) -> Batch | None:
        """Get a batch from the repository by its reference."""
        return self._batches.get(BatchReference(reference))

    def get_all(self) -> list[Batch]:
        """Get all batches from the repository."""
        return list(self._batches.values())


class FakeSession:
    """Fake database session."""

    commit_count: int = 0

    def commit(self) -> None:
        """Record a commit."""
        self.commit_count += 1

    @property
    def committed(self) -> bool:
        """Check if the session was ever committed."""
        return self.commit_count > 0


@dataclass
class FakeUnitOfWork(UnitOfWork):
    """Fake Unit of Work."""

    batches: FakeRepository = field(default_factory=FakeRepository)
    commit_count: int = 0

    def commit(self):
        """Record a commit."""
        self.commit_count += 1

    def rollback(self):
        """Pretend to rollback."""

    @property
    def committed(self) -> bool:
        """Check if the session was ever committed."""
        return self.commit_count > 0


def test_returns_allocation() -> None:
    """services.allocate should return the batch reference."""
    uow = FakeUnitOfWork()

    line = OrderLine(OrderReference("o1"), SKU("COMPLICATED-LAMP"), 10)

    services.add_batch(
        services.BatchCandidate("b1", "COMPLICATED-LAMP", 100, date(2010, 1, 1)), uow
    )

    result = services.allocate(line, uow)

    assert result == "b1"


def test_error_for_invalid_sku() -> None:
    """services.allocate should throw in case the SKU is invalid."""
    uow = FakeUnitOfWork()

    line = OrderLine(OrderReference("o1"), SKU("NONEXISTENTSKU"), 10)

    services.add_batch(
        services.BatchCandidate("b1", "AREALSKU", 100, date(2010, 1, 1)), uow
    )

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate(line, uow)

    assert uow.commit_count == 1


def test_commits() -> None:
    """services.allocate should commit to the database."""
    uow = FakeUnitOfWork()

    line = OrderLine(OrderReference("o1"), SKU("OMINOUS-MIRROR"), 10)

    services.add_batch(
        services.BatchCandidate("b1", "OMINOUS-MIRROR", 100, date(2010, 1, 1)),
        uow,
    )
    services.allocate(line, uow)

    assert uow.commit_count == 2


def test_add_batch() -> None:
    """services.add_batch should successfully add a batch."""
    uow = FakeUnitOfWork()

    services.add_batch(
        services.BatchCandidate("b1", "CRUNCHY-ARMCHAIR", 100, date(2010, 1, 1)), uow
    )

    assert uow.batches.get("b1") is not None
    assert uow.committed
