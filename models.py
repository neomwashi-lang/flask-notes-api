"""Database models: User and Note."""
from sqlalchemy.orm import validates

from extensions import bcrypt, db

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72  # bcrypt ignores or rejects anything longer


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    _password_hash = db.Column("password_hash", db.String(128), nullable=False)

    # Deleting a user also deletes their notes.
    notes = db.relationship(
        "Note", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def password_hash(self):
        raise AttributeError("Password hashes cannot be read.")

    @password_hash.setter
    def password_hash(self, password):
        """Hash the plain-text password with bcrypt; the original is never stored."""
        if not password or len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
            )
        if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError("Password is too long.")
        self._password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    @validates("username")
    def validate_username(self, _key, value):
        value = (value or "").strip()
        if not 3 <= len(value) <= 30:
            raise ValueError("Username must be between 3 and 30 characters long.")
        return value

    def to_dict(self):
        return {"id": self.id, "username": self.username}


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30), nullable=False, default="general")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    user = db.relationship("User", back_populates="notes")

    @validates("title")
    def validate_title(self, _key, value):
        value = (value or "").strip()
        if not 1 <= len(value) <= 100:
            raise ValueError("Title must be between 1 and 100 characters long.")
        return value

    @validates("content")
    def validate_content(self, _key, value):
        value = (value or "").strip()
        if not value:
            raise ValueError("Content cannot be empty.")
        return value

    @validates("category")
    def validate_category(self, _key, value):
        value = (value or "").strip()
        if not value:
            return "general"
        if len(value) > 30:
            raise ValueError("Category must be 30 characters or fewer.")
        return value

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
