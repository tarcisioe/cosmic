"""Tests for the Unit of Work implementation."""
from datetime import date

import pytest
from sqlalchemy.orm import Session

from cosmic.domain.batch import BatchReference
from cosmic.domain.order import SKU, OrderLine, OrderReference
from cosmic.service_layer.services import BatchCandidate
from cosmic.sqlalchemy.unit_of_work import SessionFactory, SQLAlchemyUnitOfWork


def insert_batch(session: Session, candidate: BatchCandidate) -> None:
    """Insert a batch into the database for testing."""
    session.execute(
        "INSERT INTO batches (reference, sku, quantity, eta)"
        " VALUES (:ref, :sku, :qty, :eta)",
        {
            "ref": candidate.reference,
            "sku": candidate.sku,
            "qty": candidate.quantity,
            "eta": candidate.eta,
        },
    )


def get_allocated_batch_ref(
    session: Session, order_id: str, sku: str
) -> BatchReference:
    """Get the allocated batch reference given the requested order_id."""
    [[order_line_id]] = session.execute(
        "SELECT id FROM order_lines WHERE `order`=:order AND sku=:sku",
        {"order": order_id, "sku": sku},
    )

    [[batchref]] = session.execute(
        "SELECT b.reference FROM allocations JOIN batches AS b ON batch_id = b.id"
        " WHERE orderline_id=:orderline_id",
        {"orderline_id": order_line_id},
    )

    return BatchReference(batchref)


def test_uow_can_retrieve_a_batch_and_allocate_to_it(
    session_factory: SessionFactory,
) -> None:
    """UoW should be able to retrieve a batch and allocate to it."""
    session = session_factory()

    insert_batch(
        session, BatchCandidate("batch1", "HIPSTER-WORKBENCH", 100, date(2010, 1, 1))
    )

    session.commit()

    with SQLAlchemyUnitOfWork(session_factory) as uow:
        batch = uow.batches.get(batch_reference="batch1")
        assert batch is not None
        line = OrderLine(OrderReference("o1"), SKU("HIPSTER-WORKBENCH"), 10)
        batch.allocate(line)
        uow.commit()

    batchref = get_allocated_batch_ref(session, "o1", "HIPSTER-WORKBENCH")
    assert batchref == "batch1"


def test_rolls_back_uncommitted_work_by_default(
    session_factory: SessionFactory,
) -> None:
    """UoW should roll back uncommitted work."""
    uow = SQLAlchemyUnitOfWork(session_factory)

    with uow:
        insert_batch(
            uow.session,
            BatchCandidate("batch1", "MEDIUM-PLINTH", 100, date(2010, 1, 1)),
        )

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert not rows


def test_rolls_back_on_error(session_factory: SessionFactory) -> None:
    """UoW should roll back in case of error."""

    class MyException(Exception):
        """Dummy exception."""

    uow = SQLAlchemyUnitOfWork(session_factory)

    with pytest.raises(MyException):
        with uow:
            insert_batch(
                uow.session,
                BatchCandidate("batch1", "LARGE-FORK", 100, date(2010, 1, 1)),
            )
            raise MyException()

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert not rows
