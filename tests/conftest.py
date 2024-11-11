import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.database import Base, get_db
from app.main import app
from app.receipt_approver.models import ReceiptApproverResponse  # noqa: F401

# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger(__name__)


# Fixture to create all tables before each test and drop after
@pytest.fixture(scope="function")
def test_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    yield session
    # Drop tables
    session.close()
    Base.metadata.drop_all(bind=engine)


# Override the get_db function to use the test session
@pytest.fixture(scope="module")
def client():
    def override_get_db():
        logger.info("<<<<<< overridden db used")
        Base.metadata.create_all(bind=engine)
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Override the FastAPI dependency
    app.dependency_overrides[get_db] = override_get_db

    # Use FastAPI test client
    with TestClient(app) as c:
        yield c
