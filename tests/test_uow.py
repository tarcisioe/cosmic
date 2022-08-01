"""Tests for the Unit of Work implementation."""
from datetime import date

import pytest
from sqlalchemy.orm import Session

from cosmic.domain.batch import BatchCandidate, BatchReference
from cosmic.domain.order import SKU, OrderLine, OrderReference
from cosmic.sqlalchemy.unit_of_work import SessionFactory, SQLAlchemyUnitOfWork


def insert_batch(
    session: Session, candidate: BatchCandidate, product_version_number: int = 0
) -> None:
    """Insert a batch into the database for testing."""
    session.execute(
        "INSERT INTO products (sku, version_number) VALUES (:sku, :version_number)",
        {
            "sku": candidate.sku,
            "version_number": product_version_number,
        },
    )
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
        product = uow.products.get(sku="HIPSTER-WORKBENCH")
        assert product is not None
        line = OrderLine(OrderReference("o1"), SKU("HIPSTER-WORKBENCH"), 10)
        product.allocate(line)
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


@pytest.mark.skip("Requires postgres.")
def test_concurrent_updates_to_version_are_not_allowed(
    postgres_session_factory: SessionFactory,
):
    """Concurrent updates to the same Product should not go through."""
    sku, batch = SKU("PRODUCT1"), SKU("BATCH1")
    session = postgres_session_factory()

    insert_batch(
        session,
        BatchCandidate(batch, sku, 100, eta=date(2022, 1, 1)),
        product_version_number=1,
    )
    session.commit()

    line1 = OrderLine(OrderReference("ORDER1"), sku, 1)
    line2 = OrderLine(OrderReference("ORDER2"), sku, 1)

    with (
        SQLAlchemyUnitOfWork(postgres_session_factory) as uow1,
        SQLAlchemyUnitOfWork(postgres_session_factory) as uow2,
    ):
        products1 = uow1.products.get(sku)
        assert products1 is not None

        products2 = uow1.products.get(sku)
        assert products2 is not None

        products1.allocate(line1)
        products2.allocate(line2)

        uow1.commit()
        uow2.commit()

    [[version]] = session.execute(
        "SELECT version_number FROM products WHERE sku=:sku",
        {"sku": sku},
    )

    assert version == 2

    orders = session.execute(
        "SELECT orderid FROM allocations"
        " JOIN batches ON allocations.batch_id = batches.id"
        " JOIN order_lines ON allocations.orderline_id = order_lines.id"
        " WHERE order_lines.sku=:sku",
        {"sku": sku},
    )

    assert orders.rowcount == 1  # type: ignore

    with SQLAlchemyUnitOfWork(postgres_session_factory) as uow:
        uow.session.execute("select 1")
