"""HTTP API using FastAPI."""
from datetime import datetime

from fastapi import FastAPI, Response
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .domain.order import SKU, OrderLine, OrderReference
from .messagebus import MessageBus
from .service_layer import services
from .service_layer.unit_of_work import TrackingUnitOfWork
from .sqlalchemy.unit_of_work import SQLAlchemyUnitOfWork


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


def make_api(engine: Engine, messagebus: MessageBus):
    """Create the API."""
    app = FastAPI()

    def get_session() -> Session:
        return Session(engine)

    @app.post("/allocate/", status_code=201)
    async def allocate_endpoint(
        data: AllocateRequest, response: Response
    ) -> AllocateResponse | ErrorResponse:
        order_line = OrderLine(
            OrderReference(data.orderid),
            SKU(data.sku),
            data.qty,
        )

        uow = TrackingUnitOfWork(SQLAlchemyUnitOfWork(get_session), messagebus)

        try:
            batch = services.allocate(order_line, uow)
        except (services.OutOfStock, services.InvalidSku) as exc:
            response.status_code = 400
            return ErrorResponse(message=str(exc))

        return AllocateResponse(batchref=batch)

    @app.post("/add_batch/", status_code=201)
    async def add_batch(data: AddBatchRequest) -> str:
        eta = datetime.fromisoformat(data.eta).date()

        uow = TrackingUnitOfWork(SQLAlchemyUnitOfWork(get_session), messagebus)

        services.add_batch(
            services.BatchCandidate(data.ref, data.sku, data.qty, eta), uow
        )

        return "OK"

    return app
