"""Shared fixtures. Every test gets its own empty in-memory database."""
import pytest

from app import create_app
from config import TestConfig
from extensions import db
from models import User

PASSWORD = "password123"


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A client with no login cookie."""
    return app.test_client()


@pytest.fixture
def create_user(app):
    """Insert a user straight into the database and return its id."""

    def _create(username="alice", password=PASSWORD):
        with app.app_context():
            user = User(username=username)
            user.password_hash = password
            db.session.add(user)
            db.session.commit()
            return user.id

    return _create


@pytest.fixture
def logged_in_client(app, create_user):
    """Return a function that makes a new client logged in as the given user.

    Each client has its own cookie jar, so two users can act at the same time.
    """

    def _make(username="alice"):
        create_user(username)
        client = app.test_client()
        response = client.post(
            "/login", json={"username": username, "password": PASSWORD}
        )
        assert response.status_code == 200
        return client

    return _make
