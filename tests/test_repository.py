"""Tests for the SQLAlchemy repository."""
# pylint: disable=redefined-outer-name
import logging
from datetime import date
from typing import Iterable

import pytest
from sqlalchemy.orm import Session

from cosmic.batch import SKU, Batch, BatchReference
from cosmic.order import OrderLine, OrderReference
from cosmic.repository import Repository
from cosmic.sqlalchemy.repository import SQLAlchemyRepository

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


# pylint: disable=unused-argument


@pytest.fixture(scope="session")
def sqlalchemy_mappings() -> None:
    """Start sqlalchemy mappings for tests."""
    from cosmic.sqlalchemy.mappings import start_mappings

    start_mappings()


@pytest.fixture
def session(sqlalchemy_mappings: None) -> Iterable[Session]:
    """Get a working SQLAlchemy Session."""
    from sqlalchemy import create_engine

    from cosmic.sqlalchemy.mappings import create_schema

    engine = create_engine("sqlite://")
    create_schema(engine)

    with Session(engine) as sqlite_session:
        yield sqlite_session


# pylint: enable=unused-argument


def test_repository_can_save_a_batch(session: Session) -> None:
    """SQLAlchemyRepository should successfully save a batch."""
    batch = Batch(
        BatchReference("batch1"), SKU("RUSTY-SOAPDISH"), 100, eta=date(2022, 7, 6)
    )

    repository: Repository = SQLAlchemyRepository(session)
    repository.add(batch)
    session.commit()

    rows = session.execute('SELECT reference, sku, quantity, eta FROM "batches"')
    assert list(rows) == [("batch1", "RUSTY-SOAPDISH", 100, "2022-07-06")]


def test_repository_can_retrieve_a_batch_with_allocations(session: Session) -> None:
    """SQLAlchemyRepository should retrieve a batch with allocations from the database."""

    def insert_order_line(session: Session) -> int:
        session.execute(
            "INSERT INTO order_lines ('order', sku, quantity)"
            ' VALUES ("order1", "GENERIC-SOFA", 12)'
        )

        # TODO: check why this isn't working properly
        # [[orderline_id]] = session.execute(
        #     "SELECT id FROM order_lines WHERE 'order'=:order AND sku=:sku",
        #     {"order": "order1", "sku": "GENERIC-SOFA"},
        # )

        return 1

    def insert_batch(session: Session, batch_reference: BatchReference) -> int:
        session.execute(
            "INSERT INTO batches (reference, sku, quantity, eta)"
            ' VALUES (:batch_reference, "GENERIC-SOFA", 12, "2022-07-06")',
            {"batch_reference": batch_reference},
        )

        [[batch_id]] = session.execute(
            "SELECT id FROM batches WHERE reference=:batch_reference",
            {"batch_reference": batch_reference},
        )

        return batch_id

    def insert_allocation(session: Session, orderline_id: int, batch_id: int) -> None:
        session.execute(
            "INSERT INTO allocations (orderline_id, batch_id)"
            " VALUES (:orderline_id, :batch_id)",
            {"orderline_id": orderline_id, "batch_id": batch_id},
        )

    batch1_reference = BatchReference("batch1")
    batch2_reference = BatchReference("batch2")

    orderline_id = insert_order_line(session)
    batch1_id = insert_batch(session, batch1_reference)
    insert_batch(session, batch2_reference)
    insert_allocation(session, orderline_id, batch1_id)

    repository: Repository = SQLAlchemyRepository(session)
    retrieved = repository.get(batch1_reference)

    expected = Batch(batch1_reference, SKU("GENERIC-SOFA"), 100, eta=date(2022, 7, 6))
    assert retrieved == expected
    assert retrieved.sku == expected.sku
    assert retrieved._allocated == {
        OrderLine(OrderReference("order1"), SKU("GENERIC-SOFA"), 12),
    }
