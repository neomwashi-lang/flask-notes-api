import pytest

SIGNUP = {
    "username": "neo",
    "password": "secret123",
    "password_confirmation": "secret123",
}


def test_signup_creates_user_and_logs_in(client):
    response = client.post("/signup", json=SIGNUP)
    assert response.status_code == 201
    assert response.get_json() == {"id": 1, "username": "neo"}
    assert "password" not in response.get_data(as_text=True)
    assert client.get("/check_session").status_code == 200


def test_signup_rejects_duplicate_username(client):
    client.post("/signup", json=SIGNUP)
    response = client.post("/signup", json=SIGNUP)
    assert response.status_code == 409
    assert response.get_json()["errors"] == ["Username is already taken."]


@pytest.mark.parametrize(
    "changes",
    [
        {"username": "ab"},
        {"username": ""},
        {"password": "short", "password_confirmation": "short"},
        {"password_confirmation": "different123"},
        {"username": 123},
        {"password": ["not", "text"]},
    ],
)
def test_signup_validation_errors(client, changes):
    response = client.post("/signup", json={**SIGNUP, **changes})
    assert response.status_code == 422
    assert response.get_json()["errors"]
    assert client.get("/check_session").status_code == 401


def test_signup_with_no_json_body(client):
    response = client.post("/signup", data="not json", content_type="application/json")
    assert response.status_code == 422


def test_login_success(client, create_user):
    create_user("alice")
    response = client.post(
        "/login", json={"username": "alice", "password": "password123"}
    )
    assert response.status_code == 200
    assert response.get_json()["username"] == "alice"
    assert client.get("/check_session").get_json()["username"] == "alice"


@pytest.mark.parametrize(
    "credentials",
    [
        {"username": "alice", "password": "wrong-password"},
        {"username": "nobody", "password": "password123"},
    ],
)
def test_login_with_bad_credentials_returns_401(client, create_user, credentials):
    create_user("alice")
    response = client.post("/login", json=credentials)
    assert response.status_code == 401
    assert response.get_json()["errors"] == ["Invalid username or password."]
    assert client.get("/check_session").status_code == 401


def test_login_requires_username_and_password(client):
    response = client.post("/login", json={"username": "alice"})
    assert response.status_code == 422


def test_check_session_when_logged_out(client):
    response = client.get("/check_session")
    assert response.status_code == 401
    assert response.get_json() == {}


def test_check_session_when_logged_in(logged_in_client):
    client = logged_in_client("alice")
    response = client.get("/check_session")
    assert response.status_code == 200
    assert response.get_json()["username"] == "alice"


def test_logout_ends_the_session(logged_in_client):
    client = logged_in_client("alice")
    assert client.delete("/logout").status_code == 204
    assert client.get("/check_session").status_code == 401
    assert client.get("/notes").status_code == 401


def test_wrong_method_returns_json_error(client):
    response = client.get("/login")
    assert response.status_code == 405
    assert "errors" in response.get_json()
