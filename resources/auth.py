"""Session-based authentication: signup, login, check_session, logout.

After a successful signup or login the user's id is stored in Flask's signed
session cookie. The browser sends that cookie back on every request.
"""
from functools import wraps

from flask import g, request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import User


def get_json_body():
    """Return the request's JSON body as a dict ({} if missing or malformed)."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def as_text(value):
    """Treat anything that is not a string as empty, so validators get text."""
    return value if isinstance(value, str) else ""


def current_user():
    """Return the logged-in User, or None if nobody is logged in."""
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def login_required(view):
    """Reject the request with 401 unless a user is logged in.

    The logged-in user is made available as g.current_user.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            return {"errors": ["Unauthorized: please log in."]}, 401
        g.current_user = user
        return view(*args, **kwargs)

    return wrapper


class Signup(Resource):
    def post(self):
        data = get_json_body()
        username = as_text(data.get("username"))
        password = as_text(data.get("password"))
        confirmation = as_text(data.get("password_confirmation"))

        user = User()
        errors = []
        try:
            user.username = username
        except ValueError as error:
            errors.append(str(error))
        try:
            user.password_hash = password
        except ValueError as error:
            errors.append(str(error))
        if password != confirmation:
            errors.append("Password and password confirmation do not match.")
        if errors:
            return {"errors": errors}, 422

        if User.query.filter_by(username=user.username).first():
            return {"errors": ["Username is already taken."]}, 409

        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:  # two signups with the same name at once
            db.session.rollback()
            return {"errors": ["Username is already taken."]}, 409

        session.clear()
        session["user_id"] = user.id
        return user.to_dict(), 201


class Login(Resource):
    def post(self):
        data = get_json_body()
        username = as_text(data.get("username")).strip()
        password = as_text(data.get("password"))

        if not username or not password:
            return {"errors": ["Username and password are required."]}, 422

        user = User.query.filter_by(username=username).first()
        if user is None or not user.authenticate(password):
            # Same message for both cases so usernames cannot be probed.
            return {"errors": ["Invalid username or password."]}, 401

        session.clear()
        session["user_id"] = user.id
        return user.to_dict(), 200


class CheckSession(Resource):
    def get(self):
        user = current_user()
        if user is None:
            session.pop("user_id", None)  # drop a cookie for a deleted user
            return {}, 401
        return user.to_dict(), 200


class Logout(Resource):
    def delete(self):
        session.pop("user_id", None)
        return {}, 204
