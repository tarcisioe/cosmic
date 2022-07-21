"""HTTP API using FastAPI."""
from datetime import datetime

from fastapi import FastAPI, Response
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from . import services
from .domain.order import SKU, OrderLine, OrderReference
from .sqlalchemy.repository import SQLAlchemyRepository


class AllocateRequest(BaseModel):
    """Data for the allocation request."""

    orderid: str
    sku: str
    qty: int


class ErrorResponse(BaseModel):
    """Data when an error occurs."""

    message: str


class AllocateResponse(BaseModel):
    """Data for the allocation response."""

    batchref: str


class AddBatchRequest(BaseModel):
    """Data for the allocation request."""

    ref: str
    sku: str
    qty: int
    eta: str


def make_api(engine: Engine):
    """Create the API."""
    app = FastAPI()

    @app.post("/allocate/", status_code=201)
    async def allocate_endpoint(
        data: AllocateRequest, response: Response
    ) -> AllocateResponse | ErrorResponse:
        order_line = OrderLine(
            OrderReference(data.orderid),
            SKU(data.sku),
            data.qty,
        )

        with Session(engine) as session:
            repository = SQLAlchemyRepository(session)

            try:
                batch = services.allocate(order_line, repository, session)
            except (services.OutOfStock, services.InvalidSku) as exc:
                response.status_code = 400
                return ErrorResponse(message=str(exc))

            session.commit()

        return AllocateResponse(batchref=batch)

    @app.post("/add_batch/", status_code=201)
    async def add_batch(data: AddBatchRequest) -> str:
        eta = datetime.fromisoformat(data.eta).date()

        with Session(engine) as session:
            repository = SQLAlchemyRepository(session)

            services.add_batch(
                services.BatchCandidate(data.ref, data.sku, data.qty, eta),
                repository,
                session,
            )

        return "OK"

    return app
