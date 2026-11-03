import pytest
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Note, User


def make_user(username="alice", password="password123"):
    user = User(username=username)
    user.password_hash = password
    return user


def test_password_is_hashed_not_stored_in_plain_text(app):
    with app.app_context():
        user = make_user()
        db.session.add(user)
        db.session.commit()
        assert user._password_hash != "password123"
        assert user._password_hash.startswith("$2b$")


def test_password_hash_cannot_be_read(app):
    with app.app_context():
        with pytest.raises(AttributeError):
            make_user().password_hash


def test_authenticate(app):
    with app.app_context():
        user = make_user()
        assert user.authenticate("password123") is True
        assert user.authenticate("wrong-password") is False


@pytest.mark.parametrize("username", ["", "  ", "ab", "x" * 31, None])
def test_invalid_usernames_are_rejected(app, username):
    with app.app_context():
        with pytest.raises(ValueError):
            User(username=username)


@pytest.mark.parametrize("password", ["", "short", None, "x" * 100])
def test_invalid_passwords_are_rejected(app, password):
    with app.app_context():
        with pytest.raises(ValueError):
            make_user().password_hash = password


def test_usernames_must_be_unique(app):
    with app.app_context():
        db.session.add(make_user("alice"))
        db.session.commit()
        db.session.add(make_user("alice"))
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_note_validation(app):
    with app.app_context():
        with pytest.raises(ValueError):
            Note(title="", content="x")
        with pytest.raises(ValueError):
            Note(title="x" * 101, content="x")
        with pytest.raises(ValueError):
            Note(title="Title", content="   ")


def test_note_category_defaults_to_general(app):
    with app.app_context():
        user = make_user()
        user.notes.append(Note(title="Title", content="Content"))
        db.session.add(user)
        db.session.commit()
        assert user.notes[0].category == "general"


def test_deleting_a_user_deletes_their_notes(app):
    with app.app_context():
        user = make_user()
        user.notes.append(Note(title="Title", content="Content"))
        db.session.add(user)
        db.session.commit()
        db.session.delete(user)
        db.session.commit()
        assert Note.query.count() == 0
