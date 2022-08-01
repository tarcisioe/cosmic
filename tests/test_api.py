"""End-to-end API tests."""
# pylint: disable=redefined-outer-name
from dataclasses import dataclass, field
from typing import AsyncIterator

import pytest
import pytest_asyncio
from httpx import AsyncClient, Response
from sqlalchemy.engine import Engine

from cosmic.domain.events import OutOfStock
from cosmic.domain.order import SKU
from cosmic.messagebus import MessageBus


@dataclass
class FakeOutOfStockHandler:
    """Fake handler for OutOfStock events."""

    events_registered: list[OutOfStock] = field(default_factory=list)

    def __call__(self, event: OutOfStock) -> None:
        self.events_registered.append(event)


@dataclass
class APITestTools:
    """Fixture for API test utilities."""

    client: AsyncClient
    url: str
    out_of_stock_handler: FakeOutOfStockHandler


@pytest_asyncio.fixture
async def api(test_db_engine: Engine) -> AsyncIterator[APITestTools]:
    """Create a test API client."""
    from cosmic.http_api import make_api

    url = "http://test"

    fake_out_of_stockhandler = FakeOutOfStockHandler()

    messagebus = MessageBus()
    messagebus.add_handler(OutOfStock, fake_out_of_stockhandler)

    async with AsyncClient(
        app=make_api(test_db_engine, messagebus), base_url=url
    ) as client:
        yield APITestTools(client, url, fake_out_of_stockhandler)


async def post_to_add_batch(
    api: APITestTools, ref: str, sku: str, qty: int, eta: str
) -> Response:
    """Post to add_batch/ on the API."""
    return await api.client.post(
        f"{api.url}/add_batch/",
        json={"ref": ref, "sku": sku, "qty": qty, "eta": eta},
    )


@pytest.mark.asyncio
async def test_api_returns_allocation(api: APITestTools) -> None:
    """HTTP API should return a reference to the batch allocated."""

    sku, othersku = "PRODUCT1", "PRODUCT2"

    earlybatch = "BATCH1"
    laterbatch = "BATCH2"
    otherbatch = "BATCH3"

    response = await post_to_add_batch(api, laterbatch, sku, 100, "2011-01-02")
    assert response.status_code == 201
    response = await post_to_add_batch(api, earlybatch, sku, 100, "2011-01-01")
    assert response.status_code == 201
    response = await post_to_add_batch(api, otherbatch, othersku, 100, "2010-12-01")
    assert response.status_code == 201

    data = {"orderid": "ORDER1", "sku": sku, "qty": 3}

    response = await api.client.post(f"{api.url}/allocate/", json=data)

    assert response.status_code == 201
    assert response.json()["batchref"] == earlybatch


@pytest.mark.asyncio
async def test_allocations_are_persisted(api: APITestTools):
    """HTTP API should persist the modifications."""
    sku = "PRODUCT1"
    batch1, batch2 = "BATCH1", "BATCH2"
    order1, order2 = "ORDER1", "ORDER2"

    response = await post_to_add_batch(api, batch1, sku, 10, "2011-01-01")
    assert response.status_code == 201
    response = await post_to_add_batch(api, batch2, sku, 10, "2011-01-02")
    assert response.status_code == 201

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
async def test_400_message_for_out_of_stock(api: APITestTools):
    """HTTP API should return 400 when we are out of stock."""
    sku = SKU("PRODUCT1")
    small_batch = "BATCH1"
    large_order = "ORDER1"

    response = await post_to_add_batch(api, small_batch, sku, 10, "2011-01-01")
    assert response.status_code == 201

    data = {"orderid": large_order, "sku": sku, "qty": 20}

    response = await api.client.post(f"{api.url}/allocate/", json=data)

    assert response.status_code == 400
    assert response.json()["message"] == f"Out of stock for sku {sku}"

    assert api.out_of_stock_handler.events_registered == [OutOfStock(sku)]


@pytest.mark.asyncio
async def test_400_message_for_invalid_sku(api: APITestTools):
    """HTTP API should return 400 when the product is invalid."""
    unknown_sku = SKU("PRODUCT1")
    orderid = "ORDER1"

    data = {"orderid": orderid, "sku": unknown_sku, "qty": 20}

    response = await api.client.post(f"{api.url}/allocate/", json=data)

    assert response.status_code == 400
    assert response.json()["message"] == f"Invalid sku {unknown_sku}"
