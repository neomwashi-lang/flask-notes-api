"""API resources. Each module defines Flask-RESTful Resource classes."""
from resources.auth import CheckSession, Login, Logout, Signup
from resources.notes import NoteDetail, NoteList


def register_resources(api):
    """Attach every resource to the Flask-RESTful Api."""
    api.add_resource(Signup, "/signup")
    api.add_resource(Login, "/login")
    api.add_resource(CheckSession, "/check_session")
    api.add_resource(Logout, "/logout")
    api.add_resource(NoteList, "/notes")
    api.add_resource(NoteDetail, "/notes/<int:note_id>")
