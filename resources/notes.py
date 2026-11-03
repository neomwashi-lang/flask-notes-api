"""Notes resource: full CRUD, scoped to the logged-in user.

Every route requires login (see login_required). A user can only see and
change their own notes: another user's note returns 403.
"""
from flask import g, request
from flask_restful import Resource

from extensions import db
from models import Note
from resources.auth import get_json_body, login_required

NOTE_FIELDS = ("title", "content", "category")
DEFAULT_PER_PAGE = 10
MAX_PER_PAGE = 50


def apply_fields(note, data):
    """Copy title/content/category from data onto note.

    Returns a list of error messages (empty if everything was valid).
    The model validators do the actual checking.
    """
    errors = []
    for field in NOTE_FIELDS:
        if field not in data:
            continue
        value = data[field]
        if not isinstance(value, str):
            errors.append(f"{field.capitalize()} must be text.")
            continue
        try:
            setattr(note, field, value)
        except ValueError as error:
            errors.append(str(error))
    return errors


def get_owned_note(note_id):
    """Return (note, None) or (None, error_response) for the logged-in user."""
    note = db.session.get(Note, note_id)
    if note is None:
        return None, ({"errors": ["Note not found."]}, 404)
    if note.user_id != g.current_user.id:
        return None, ({"errors": ["You do not have permission to access this note."]}, 403)
    return note, None


def read_positive_int(name, default):
    """Read a positive integer query parameter. Returns (value, error_message)."""
    raw = request.args.get(name)
    if raw is None:
        return default, None
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value < 1:
        return None, f"{name} must be a positive whole number."
    return value, None


class NoteList(Resource):
    method_decorators = [login_required]

    def get(self):
        """List the current user's notes, newest first, one page at a time."""
        page, page_error = read_positive_int("page", 1)
        per_page, per_page_error = read_positive_int("per_page", DEFAULT_PER_PAGE)
        errors = [e for e in (page_error, per_page_error) if e]
        if errors:
            return {"errors": errors}, 422

        pagination = (
            Note.query.filter_by(user_id=g.current_user.id)
            .order_by(Note.created_at.desc(), Note.id.desc())
            .paginate(
                page=page, per_page=per_page, max_per_page=MAX_PER_PAGE, error_out=False
            )
        )
        return {
            "notes": [note.to_dict() for note in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }, 200

    def post(self):
        """Create a note owned by the current user."""
        data = get_json_body()
        data.setdefault("title", "")  # missing required fields fail validation
        data.setdefault("content", "")

        note = Note(user_id=g.current_user.id)
        errors = apply_fields(note, data)
        if errors:
            return {"errors": errors}, 422

        db.session.add(note)
        db.session.commit()
        return note.to_dict(), 201


class NoteDetail(Resource):
    method_decorators = [login_required]

    def get(self, note_id):
        note, error = get_owned_note(note_id)
        if error:
            return error
        return note.to_dict(), 200

    def patch(self, note_id):
        """Update only the fields that were sent."""
        note, error = get_owned_note(note_id)
        if error:
            return error

        data = get_json_body()
        if not any(field in data for field in NOTE_FIELDS):
            return {"errors": ["Provide at least one of: title, content, category."]}, 422

        errors = apply_fields(note, data)
        if errors:
            db.session.rollback()  # discard any field that was already applied
            return {"errors": errors}, 422

        db.session.commit()
        return note.to_dict(), 200

    def delete(self, note_id):
        note, error = get_owned_note(note_id)
        if error:
            return error
        db.session.delete(note)
        db.session.commit()
        return {}, 204
