"""End-to-end API tests."""
# pylint: disable=redefined-outer-name
from dataclasses import dataclass
from datetime import date
from typing import AsyncIterator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from cosmic.domain.batch import Batch, BatchReference
from cosmic.domain.order import SKU


@dataclass
class APITestTools:
    """Fixture for API test utilities."""

    client: AsyncClient
    url: str


@pytest_asyncio.fixture
async def api(test_db_engine: Engine) -> AsyncIterator[APITestTools]:
    """Create a test API client."""
    from cosmic.http_api import make_api

    url = "http://test"

    async with AsyncClient(app=make_api(test_db_engine), base_url=url) as client:
        yield APITestTools(client, url)


def add_batches(session: Session, batches: list[Batch]) -> None:
    """Populate a database with batches."""
    for batch in batches:
        session.add(batch)
    session.commit()


@pytest.mark.asyncio
async def test_api_returns_allocation(
    test_db_session: Session, api: APITestTools
) -> None:
    """HTTP API should return a reference to the batch allocated."""
    sku, othersku = SKU("PRODUCT1"), SKU("PRODUCT2")

    earlybatch = BatchReference("BATCH1")
    laterbatch = BatchReference("BATCH2")
    otherbatch = BatchReference("BATCH3")

    add_batches(
        test_db_session,
        [
            Batch(laterbatch, sku, 100, date(2011, 1, 2)),
            Batch(earlybatch, sku, 100, date(2011, 1, 1)),
            Batch(otherbatch, othersku, 100, date(2010, 1, 1)),
        ],
    )

    data = {"orderid": "ORDER1", "sku": sku, "qty": 3}

    response = await api.client.post(f"{api.url}/allocate/", json=data)

    assert response.status_code == 201
    assert response.json()["batchref"] == earlybatch


@pytest.mark.asyncio
async def test_allocations_are_persisted(test_db_session: Session, api: APITestTools):
    """HTTP API should persist the modifications."""
    sku = SKU("PRODUCT1")
    batch1, batch2 = BatchReference("BATCH1"), BatchReference("BATCH2")
    order1, order2 = "ORDER1", "ORDER2"

    add_batches(
        test_db_session,
        [
            Batch(batch1, sku, 10, date(2011, 1, 1)),
            Batch(batch2, sku, 10, date(2011, 1, 2)),
        ],
    )

    line1 = {"orderid": order1, "sku": sku, "qty": 10}
    line2 = {"orderid": order2, "sku": sku, "qty": 10}

    # first order uses up all stock in batch 1
    response = await api.client.post(f"{api.url}/allocate/", json=line1)
    assert response.status_code == 201
    assert response.json()["batchref"] == batch1

    # second order should go to batch 2
    response = await api.client.post(f"{api.url}/allocate/", json=line2)
    assert response.status_code == 201
    assert response.json()["batchref"] == batch2


@pytest.mark.asyncio
async def test_400_message_for_out_of_stock(
    test_db_session: Session, api: APITestTools
):
    """HTTP API should return 400 when we are out of stock."""
    sku = SKU("PRODUCT1")
    small_batch = BatchReference("BATCH1")
    large_order = "ORDER1"

    add_batches(
        test_db_session,
        [
            Batch(small_batch, sku, 10, date(2011, 1, 1)),
        ],
    )

    data = {"orderid": large_order, "sku": sku, "qty": 20}

    response = await api.client.post(f"{api.url}/allocate/", json=data)

    assert response.status_code == 400
    assert response.json()["message"] == f"Out of stock for sku {sku}"


@pytest.mark.asyncio
async def test_400_message_for_invalid_sku(api: APITestTools):
    """HTTP API should return 400 when the product is invalid."""
    unknown_sku = SKU("PRODUCT1")
    orderid = "ORDER1"

    data = {"orderid": orderid, "sku": unknown_sku, "qty": 20}

    response = await api.client.post(f"{api.url}/allocate/", json=data)

    assert response.status_code == 400
    assert response.json()["message"] == f"Invalid sku {unknown_sku}"
