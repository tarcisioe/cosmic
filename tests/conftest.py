"""Pytest configurations and fixtures."""
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
from typing import Iterable

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


@pytest.fixture(scope="session")
def start_mappings() -> None:
    """Start database mappings."""
    from cosmic.sqlalchemy.mappings import start_mappings

    start_mappings()


@pytest.fixture
def test_db_engine(start_mappings: None) -> Engine:
    """Get a working SQLAlchemy Session."""
    from sqlalchemy import create_engine

    from cosmic.sqlalchemy.mappings import create_schema

    engine = create_engine("sqlite://")
    create_schema(engine)

    return engine


@pytest.fixture
def test_db_session(test_db_engine: Engine) -> Iterable[Session]:
    """Get a working SQLAlchemy Session."""
    with Session(test_db_engine) as sqlite_session:
        yield sqlite_session
