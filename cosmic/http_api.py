"""HTTP API using FastAPI."""
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


def make_api(engine: Engine):
    """Create the API."""
    app = FastAPI()

    @app.post("/allocate/", status_code=201)
    async def allocate_endpoint(
        data: AllocateRequest, response: Response
    ) -> AllocateResponse | ErrorResponse:
        with Session(engine) as session:
            repository = SQLAlchemyRepository(session)

            order_line = OrderLine(
                OrderReference(data.orderid),
                SKU(data.sku),
                data.qty,
            )

            try:
                batch = services.allocate(order_line, repository, session)
            except (services.OutOfStock, services.InvalidSku) as exc:
                response.status_code = 400
                return ErrorResponse(message=str(exc))

            session.commit()

            return AllocateResponse(batchref=batch)

    return app
