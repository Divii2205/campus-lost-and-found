"""test setup where every test gets a fresh sqlite database that is thrown away after

the real postgresql database is never touched because get_db is swapped
so the app talks to a temporary sqlite file instead
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app


# a test client that uses its own empty sqlite database
@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    # make the tables in the new test database
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    # tell the app to use the test database instead of the real one
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    # clean up after the test
    app.dependency_overrides.clear()
    engine.dispose()


# a sample item that tests can send to the api
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
