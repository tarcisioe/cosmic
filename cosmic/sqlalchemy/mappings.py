"""SQLAlchemy mappings for our data."""
from sqlalchemy import Column, Date, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine
from sqlalchemy.orm import registry

from ..batch import Batch

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


def start_sqlalchemy(engine: Engine) -> None:
    """Initialize SQLAlchemy with our schema."""
    metadata.create_all(engine)
    map_registry.map_imperatively(Batch, batches)
