"""SQLAlchemy mappings for our data."""
from sqlalchemy import Column, Date, ForeignKey, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine
from sqlalchemy.orm import registry, relationship

from ..domain.batch import Batch
from ..domain.order import OrderLine

map_registry = registry()
metadata = MetaData()

batches = Table(
    "batches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255)),
    Column("quantity", Integer, nullable=False),
    Column("eta", Date, nullable=False),
)

order_lines = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("order", String(255)),
    Column("sku", String(255)),
    Column("quantity", Integer, nullable=False),
)

allocations = Table(
    "allocations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orderline_id", ForeignKey("order_lines.id")),
    Column("batch_id", ForeignKey("batches.id")),
)


def start_mappings():
    """Start SQLAlchemy Mappings."""
    lines_mapper = map_registry.map_imperatively(OrderLine, order_lines)
    map_registry.map_imperatively(
        Batch,
        batches,
        properties={
            "_allocated": relationship(
                lines_mapper, secondary=allocations, collection_class=set
            )
        },
    )


def create_schema(engine: Engine) -> None:
    """Initialize SQLAlchemy with our schema."""
    metadata.create_all(engine)
