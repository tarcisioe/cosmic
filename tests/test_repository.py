"""Tests for the SQLAlchemy repository."""
# pylint: disable=redefined-outer-name
from datetime import date
from typing import Iterable

import pytest
from sqlalchemy.orm import Session

from cosmic.batch import SKU, Batch, BatchReference
from cosmic.repository import Repository


@pytest.fixture
def session() -> Iterable[Session]:
    """Get a working SQLAlchemy Session."""
    from sqlalchemy import create_engine

    from cosmic.sqlalchemy.mappings import start_sqlalchemy

    engine = create_engine("sqlite://")
    start_sqlalchemy(engine)

    with Session(engine) as sqlite_session:
        yield sqlite_session


def test_repository_can_save_a_batch(session: Session) -> None:
    """SQLAlchemyRepository should successfully save a batch."""
    from cosmic.sqlalchemy.repository import SQLAlchemyRepository

    batch = Batch(
        BatchReference("batch1"), SKU("RUSTY-SOAPDISH"), 100, eta=date(2022, 7, 6)
    )

    repository: Repository = SQLAlchemyRepository(session)
    repository.add(batch)
    session.commit()

    rows = session.execute('SELECT reference, sku, quantity, eta FROM "batches"')
    assert list(rows) == [("batch1", "RUSTY-SOAPDISH", 100, "2022-07-06")]
