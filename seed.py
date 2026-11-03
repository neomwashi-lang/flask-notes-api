"""Fill the database with example users and notes.

Run after applying the migrations:  python seed.py
Running it again wipes the existing users and notes first.
"""
import random

from faker import Faker

from app import app
from extensions import db
from models import Note, User

SEED_USERNAMES = ["alice", "bob", "carol"]
SEED_PASSWORD = "password123"
NOTES_PER_USER = 14  # more than one page, so pagination can be tried
CATEGORIES = ["work", "personal", "ideas", "study", "health"]

fake = Faker()


def seed():
    Faker.seed(42)
    random.seed(42)

    with app.app_context():
        Note.query.delete()
        User.query.delete()

        for username in SEED_USERNAMES:
            user = User(username=username)
            user.password_hash = SEED_PASSWORD
            for _ in range(NOTES_PER_USER):
                user.notes.append(
                    Note(
                        title=fake.sentence(nb_words=4).rstrip("."),
                        content=fake.paragraph(nb_sentences=3),
                        category=random.choice(CATEGORIES),
                    )
                )
            db.session.add(user)

        db.session.commit()
        print(f"Seeded {User.query.count()} users and {Note.query.count()} notes.")
        print(f"Log in as {', '.join(SEED_USERNAMES)} with password '{SEED_PASSWORD}'.")


if __name__ == "__main__":
    seed()
