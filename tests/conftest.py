import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import Base  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def conteudo_itsa4():
    with open(os.path.join(FIXTURES, "ITSA4_2026-10-29.md"), encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield session
    session.close()
