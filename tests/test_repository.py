"""Tests for the SQLAlchemy repository."""
# pylint: disable=redefined-outer-name
import logging
from datetime import date

from sqlalchemy.orm import Session

from cosmic.domain.batch import SKU, Batch, BatchReference
from cosmic.domain.order import OrderLine, OrderReference
from cosmic.repository import Repository
from cosmic.sqlalchemy.repository import SQLAlchemyRepository

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def test_repository_can_save_a_batch(test_db_session: Session) -> None:
    """SQLAlchemyRepository should successfully save a batch."""
    batch = Batch(
        BatchReference("batch1"), SKU("RUSTY-SOAPDISH"), 100, eta=date(2022, 7, 6)
    )

    repository: Repository = SQLAlchemyRepository(test_db_session)
    repository.add(batch)
    test_db_session.commit()

    rows = test_db_session.execute(
        'SELECT reference, sku, quantity, eta FROM "batches"'
    )
    assert list(rows) == [("batch1", "RUSTY-SOAPDISH", 100, "2022-07-06")]


def test_repository_can_retrieve_a_batch_with_allocations(
    test_db_session: Session,
) -> None:
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

    orderline_id = insert_order_line(test_db_session)
    batch1_id = insert_batch(test_db_session, batch1_reference)
    insert_batch(test_db_session, batch2_reference)
    insert_allocation(test_db_session, orderline_id, batch1_id)

    repository: Repository = SQLAlchemyRepository(test_db_session)
    retrieved = repository.get(batch1_reference)

    expected = Batch(batch1_reference, SKU("GENERIC-SOFA"), 100, eta=date(2022, 7, 6))
    assert retrieved == expected
    assert retrieved.sku == expected.sku
    assert retrieved._allocated == {
        OrderLine(OrderReference("order1"), SKU("GENERIC-SOFA"), 12),
    }
