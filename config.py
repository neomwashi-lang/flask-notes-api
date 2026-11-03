"""Application configuration."""
import os


class Config:
    # The secret key signs the session cookie. Set SECRET_KEY in the
    # environment for anything beyond local development.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class TestConfig(Config):
    """Used by pytest: throwaway in-memory database and fast password hashing."""

    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    BCRYPT_LOG_ROUNDS = 4
