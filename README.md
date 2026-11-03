# Notes API

A secure Flask REST API for a personal notes app. Users sign up, log in with
session-based authentication, and manage their own notes. Every notes route
requires login, and a user can never read or change another user's notes.

Built with Flask, Flask-RESTful, Flask-SQLAlchemy, Flask-Migrate, Flask-Bcrypt
and SQLite. It is designed to work with the provided React sessions client
(see [Frontend](#frontend)).

## Features

- Sign up, log in, check session and log out, using Flask's signed session cookie
- Passwords hashed with bcrypt, usernames unique
- Notes with full CRUD, owned by a user
- Paginated notes index
- Ownership checks on every notes route
- Consistent JSON errors: `{"errors": ["message", ...]}`
- Database migrations, a seed script, and a pytest suite

## Requirements

- **Python 3.12** (3.11 to 3.13 should also work). Python 3.14 does **not** work,
  because the pinned Flask 2.2.2 uses a function that Python 3.14 removed.
- [Pipenv](https://pipenv.pypa.io/): `pip install pipenv`
- Git
- Node.js and npm (only if you want to run the React client)

## Installation

```bash
git clone https://github.com/neomwashi-lang/flask-notes-api.git
cd flask-notes-api

# Install the dependencies from the Pipfile (including pytest) into a virtualenv
pipenv install --dev --python 3.12
pipenv shell

# Create the database tables from the migrations
flask db upgrade

# Add example users and notes
python seed.py
```

The database is a SQLite file at `instance/app.db`. Running `python seed.py`
again wipes the users and notes and recreates the examples.

The seed script creates three users (`alice`, `bob`, `carol`), all with the
password `password123`, and 14 notes for each, so pagination can be tried.

### Optional environment variables

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Signs the session cookie. Set your own for anything beyond local use | `dev-only-change-me` |
| `DATABASE_URL` | Database connection string | `sqlite:///app.db` |

## Running the API

```bash
flask run -p 5555
```

The API is then available at `http://localhost:5555`. Port 5555 matches the
`proxy` setting in the React client's `package.json`.
(`python app.py` also starts it on port 5555.)

## Running the tests

```bash
pytest
```

The tests use a separate in-memory database, so they never touch `instance/app.db`.

## API endpoints

All request and response bodies are JSON. Errors always look like
`{"errors": ["..."]}`.

### Authentication

| Method | Endpoint | Description | Success | Errors |
|---|---|---|---|---|
| POST | `/signup` | Create an account and log in. Body: `username` (3-30 chars), `password` (8+ chars), `password_confirmation` | 201 `{"id", "username"}` | 422 invalid or mismatched fields, 409 username taken |
| POST | `/login` | Log in. Body: `username`, `password` | 200 `{"id", "username"}` | 401 wrong username or password, 422 missing fields |
| GET | `/check_session` | Return the logged-in user. Used to stay logged in after a page refresh | 200 `{"id", "username"}` | 401 `{}` if not logged in |
| DELETE | `/logout` | Log out by clearing the session | 204 (no body) | none |

### Notes (login required)

| Method | Endpoint | Description | Success | Errors |
|---|---|---|---|---|
| GET | `/notes` | List your notes, newest first. Query: `page` (default 1), `per_page` (default 10, max 50) | 200 (see below) | 401, 422 invalid `page` or `per_page` |
| POST | `/notes` | Create a note. Body: `title` (1-100 chars), `content`, optional `category` (default `general`) | 201 the note | 401, 422 invalid fields |
| GET | `/notes/<id>` | Get one of your notes | 200 the note | 401, 403, 404 |
| PATCH | `/notes/<id>` | Update one or more of `title`, `content`, `category` | 200 the updated note | 401, 403, 404, 422 |
| DELETE | `/notes/<id>` | Delete a note | 204 (no body) | 401, 403, 404 |

Status codes used for access control:

- **401 Unauthorized**: you are not logged in
- **403 Forbidden**: the note exists but belongs to another user
- **404 Not Found**: no note with that id

A note looks like this:

```json
{
  "id": 1,
  "title": "Groceries",
  "content": "Milk and eggs",
  "category": "personal",
  "created_at": "2026-11-03T20:12:26",
  "updated_at": "2026-11-03T20:12:26"
}
```

The paginated list `GET /notes?page=2&per_page=5` returns:

```json
{
  "notes": [ ... ],
  "page": 2,
  "per_page": 5,
  "total": 14,
  "pages": 3
}
```

## Project structure

```
app.py            App factory, JSON error handling, entry point
config.py         Configuration (normal and test)
extensions.py     db, bcrypt and migrate instances
models.py         User and Note models
resources/
  auth.py         Signup, login, check_session, logout, login_required
  notes.py        Notes CRUD with pagination and ownership checks
seed.py           Example data
migrations/       Flask-Migrate database migrations
tests/            pytest suite
Pipfile           Dependencies
src/, public/     Provided React client
```

## Frontend

The provided React sessions client lives in `src/` and `public/`. It handles
signup, login, session check and logout. It has no screens for notes yet.

With the API running on port 5555, start the client in a second terminal:

```bash
npm install
npm start          # macOS / Linux
```

On Windows PowerShell, `npm start` fails because of the `PORT=4000` prefix in
its script, so run React directly:

```powershell
$env:PORT=4000; npx react-scripts start
```

The client opens at `http://localhost:4000` and sends its API calls to port
5555 through the `proxy` setting in `package.json`.