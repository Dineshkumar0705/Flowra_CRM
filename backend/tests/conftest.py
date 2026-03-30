"""
Pytest configuration and shared fixtures for Flowra backend tests.

Test isolation strategy:
  - Each test gets a fresh SQLite in-memory database (no Postgres needed for unit tests)
  - DB session is wrapped in a savepoint + rollback — no data persists between tests
  - Use `db` fixture for repository/service tests
  - Use `client` fixture for HTTP integration tests (overrides FastAPI's get_db dep)

Run all tests:
    pytest -v

Run just service tests:
    pytest tests/services/ -v

Run with coverage:
    pytest --cov=app --cov-report=term-missing
"""

import os
import uuid
from typing import Generator

import pytest

# Set test environment BEFORE importing app modules
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-min-32-chars-long-ok"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient

from app.models.base import Base


# ---------------------------------------------------------------------------
# SQLite in-memory engine (no Postgres required)
# ---------------------------------------------------------------------------

_TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(
    _TEST_DB_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# Create all tables once
Base.metadata.create_all(bind=engine)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# DB fixture — transaction-scoped rollback
# ---------------------------------------------------------------------------

@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """
    Provide a DB session that rolls back after each test.
    No data ever persists between tests.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    # Nested savepoints so inner transactions can commit without committing the outer
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, trans):
        if trans.nested and not trans._parent.nested:
            session.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# FastAPI test client with DB override
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Provide a TestClient with the get_db dependency overridden
    to use the test session (transaction-scoped, rolls back after each test).
    """
    from app.main import app
    from app.core.database import get_db

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Factory helpers — create test data without going through services
# ---------------------------------------------------------------------------

@pytest.fixture()
def make_user(db: Session):
    """Factory fixture to create User rows directly."""
    from app.models.user import User
    from app.core.security import hash_password

    def _make(
        email: str = None,
        name: str = "Test User",
        password: str = "testpass123",
        is_active: bool = True,
    ) -> User:
        email = email or f"user-{uuid.uuid4().hex[:8]}@test.com"
        user = User(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            hashed_password=hash_password(password),
            is_active=is_active,
        )
        db.add(user)
        db.flush()
        return user

    return _make


@pytest.fixture()
def make_workspace(db: Session):
    """Factory fixture to create Workspace rows."""
    from app.models.workspace import Workspace, WorkspaceMember, MemberRole, WorkspacePlan

    def _make(owner_id: str, name: str = "Test Agency", plan=WorkspacePlan.STARTER) -> Workspace:
        ws = Workspace(
            id=str(uuid.uuid4()),
            name=name,
            slug=f"test-{uuid.uuid4().hex[:8]}",
            owner_id=owner_id,
            plan=plan,
            settings={},
        )
        db.add(ws)
        db.flush()
        # Add owner as member
        member = WorkspaceMember(
            id=str(uuid.uuid4()),
            workspace_id=ws.id,
            user_id=owner_id,
            role=MemberRole.OWNER,
        )
        db.add(member)
        db.flush()
        return ws

    return _make


@pytest.fixture()
def make_contact(db: Session):
    """Factory fixture to create Contact rows."""
    from app.models.contact import Contact

    def _make(workspace_id: str, email: str = None, **kwargs) -> Contact:
        contact = Contact(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            first_name=kwargs.get("first_name", "Test"),
            last_name=kwargs.get("last_name", "Contact"),
            email=email or f"contact-{uuid.uuid4().hex[:8]}@test.com",
        )
        db.add(contact)
        db.flush()
        return contact

    return _make


@pytest.fixture()
def make_deal(db: Session):
    """Factory fixture to create Deal rows."""
    from app.models.deal import Deal, DealStage, DealPriority

    def _make(workspace_id: str, **kwargs) -> Deal:
        deal = Deal(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            title=kwargs.get("title", "Test Deal"),
            value=kwargs.get("value", 50000.0),
            currency=kwargs.get("currency", "INR"),
            stage=kwargs.get("stage", DealStage.NEW),
            priority=kwargs.get("priority", DealPriority.MEDIUM),
        )
        db.add(deal)
        db.flush()
        return deal

    return _make


@pytest.fixture()
def auth_headers(db: Session, make_user, make_workspace):
    """
    Return HTTP headers with a valid JWT for a fresh test user.
    Use in `client` fixture tests:
        resp = client.get("/api/v1/deals", headers=auth_headers)
    """
    user = make_user()
    workspace = make_workspace(owner_id=user.id)

    from app.core.security import create_access_token
    token = create_access_token(
        user_id=user.id,
        workspace_id=workspace.id,
        role="owner",
    )
    return {
        "Authorization": f"Bearer {token}",
        "_user": user,
        "_workspace": workspace,
        "_token": token,
    }
