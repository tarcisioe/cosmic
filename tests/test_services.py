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


def test_returns_allocation() -> None:
    """services.allocate should return the batch reference."""
    repo = FakeRepository()
    session = FakeSession()

    line = OrderLine(OrderReference("o1"), SKU("COMPLICATED-LAMP"), 10)

    services.add_batch(
        services.BatchCandidate("b1", "COMPLICATED-LAMP", 100, date(2010, 1, 1)),
        repo,
        session,
    )

    result = services.allocate(line, repo, session)

    assert result == "b1"


def test_error_for_invalid_sku() -> None:
    """services.allocate should throw in case the SKU is invalid."""
    repo = FakeRepository()
    session = FakeSession()

    line = OrderLine(OrderReference("o1"), SKU("NONEXISTENTSKU"), 10)

    services.add_batch(
        services.BatchCandidate("b1", "AREALSKU", 100, date(2010, 1, 1)),
        repo,
        session,
    )

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate(line, repo, session)

    assert session.commit_count == 1


def test_commits() -> None:
    """services.allocate should commit to the database."""
    repo = FakeRepository()
    session = FakeSession()

    line = OrderLine(OrderReference("o1"), SKU("OMINOUS-MIRROR"), 10)

    services.add_batch(
        services.BatchCandidate("b1", "OMINOUS-MIRROR", 100, date(2010, 1, 1)),
        repo,
        session,
    )
    services.allocate(line, repo, session)

    assert session.commit_count == 2


def test_add_batch() -> None:
    """services.add_batch should successfully add a batch."""
    repo = FakeRepository()
    session = FakeSession()

    services.add_batch(
        services.BatchCandidate("b1", "CRUNCHY-ARMCHAIR", 100, date(2010, 1, 1)),
        repo,
        session,
    )

    assert repo.get("b1") is not None
    assert session.committed
