"""Test setup: every test gets a fresh, throwaway SQLite database.

The production PostgreSQL database is never touched: get_db is overridden
so the app talks to a temporary SQLite file instead.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def sample_item():
    return {
        "title": "Black HP laptop charger",
        "description": "65W charger left on a desk",
        "category": "ELECTRONICS",
        "status": "FOUND",
        "location": "Central Library, 2nd floor",
        "reporter_name": "Divijaa",
        "contact": "divijaa@campus.edu",
    }
