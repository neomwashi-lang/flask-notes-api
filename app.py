"""Application factory and entry point."""
from flask import Flask, jsonify
from flask_restful import Api

from config import Config
from extensions import bcrypt, db, migrate
from resources import register_resources


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    api = Api(app)
    register_resources(api)
    register_error_handlers(app)
    return app


def register_error_handlers(app):
    """Return JSON in the {"errors": [...]} shape the frontend reads."""

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"errors": ["Not found"]}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"errors": ["Method not allowed"]}), 405


app = create_app()

if __name__ == "__main__":
    # Port 5555 matches the "proxy" setting in the frontend's package.json.
    app.run(port=5555, debug=True)
