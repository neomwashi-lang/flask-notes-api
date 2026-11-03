"""Flask extension instances.

They are created here, without an app, and attached to the app inside
create_app(). Keeping them in their own module lets models.py and the
resource modules import them without circular imports.
"""
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
