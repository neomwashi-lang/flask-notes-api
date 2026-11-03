import pytest


def create_note(client, **fields):
    payload = {"title": "A title", "content": "Some content", **fields}
    response = client.post("/notes", json=payload)
    assert response.status_code == 201
    return response.get_json()


@pytest.mark.parametrize(
    "method, url",
    [
        ("get", "/notes"),
        ("post", "/notes"),
        ("get", "/notes/1"),
        ("patch", "/notes/1"),
        ("delete", "/notes/1"),
    ],
)
def test_every_notes_route_requires_login(client, method, url):
    response = getattr(client, method)(url, json={})
    assert response.status_code == 401
    assert response.get_json()["errors"]


# ---------- create ----------

def test_create_note(logged_in_client):
    client = logged_in_client("alice")
    note = create_note(client, title="  Groceries ", category="personal")
    assert note["title"] == "Groceries"
    assert note["category"] == "personal"
    assert note["created_at"] and note["updated_at"]


def test_create_note_defaults_category(logged_in_client):
    client = logged_in_client("alice")
    assert create_note(client)["category"] == "general"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": "", "content": "x"},
        {"title": "x" * 101, "content": "x"},
        {"title": "x", "content": "   "},
        {"title": 5, "content": ["x"]},
    ],
)
def test_create_note_validation_errors(logged_in_client, payload):
    client = logged_in_client("alice")
    response = client.post("/notes", json=payload)
    assert response.status_code == 422
    assert response.get_json()["errors"]
    assert client.get("/notes").get_json()["total"] == 0


# ---------- list and pagination ----------

def test_index_is_paginated(logged_in_client):
    client = logged_in_client("alice")
    for number in range(25):
        create_note(client, title=f"Note {number}")

    page1 = client.get("/notes").get_json()
    assert (page1["page"], page1["per_page"], page1["total"], page1["pages"]) == (1, 10, 25, 3)
    assert len(page1["notes"]) == 10
    assert page1["notes"][0]["title"] == "Note 24"  # newest first

    page3 = client.get("/notes?page=3").get_json()
    assert len(page3["notes"]) == 5

    custom = client.get("/notes?page=2&per_page=20").get_json()
    assert len(custom["notes"]) == 5 and custom["pages"] == 2

    assert client.get("/notes?page=99").get_json()["notes"] == []


def test_per_page_is_capped(logged_in_client):
    client = logged_in_client("alice")
    assert client.get("/notes?per_page=1000").get_json()["per_page"] == 50


@pytest.mark.parametrize("query", ["page=0", "page=abc", "per_page=-1", "per_page=x"])
def test_bad_pagination_parameters(logged_in_client, query):
    client = logged_in_client("alice")
    assert client.get(f"/notes?{query}").status_code == 422


def test_users_only_see_their_own_notes(logged_in_client):
    alice = logged_in_client("alice")
    bob = logged_in_client("bob")
    create_note(alice, title="Alice's note")
    create_note(bob, title="Bob's note")

    alice_notes = alice.get("/notes").get_json()
    assert alice_notes["total"] == 1
    assert alice_notes["notes"][0]["title"] == "Alice's note"


# ---------- read, update, delete ----------

def test_get_one_note(logged_in_client):
    client = logged_in_client("alice")
    note = create_note(client)
    response = client.get(f"/notes/{note['id']}")
    assert response.status_code == 200
    assert response.get_json() == note


def test_missing_note_returns_404(logged_in_client):
    client = logged_in_client("alice")
    for method in ("get", "patch", "delete"):
        assert getattr(client, method)("/notes/999", json={"title": "x"}).status_code == 404


def test_patch_updates_only_sent_fields(logged_in_client):
    client = logged_in_client("alice")
    note = create_note(client, title="Original", content="Original content")
    response = client.patch(f"/notes/{note['id']}", json={"content": "New content"})
    assert response.status_code == 200
    updated = response.get_json()
    assert updated["content"] == "New content"
    assert updated["title"] == "Original"


def test_patch_with_invalid_data_changes_nothing(logged_in_client):
    client = logged_in_client("alice")
    note = create_note(client, title="Original")
    response = client.patch(
        f"/notes/{note['id']}", json={"title": "Changed", "content": "   "}
    )
    assert response.status_code == 422
    assert client.get(f"/notes/{note['id']}").get_json()["title"] == "Original"


def test_patch_with_no_valid_fields(logged_in_client):
    client = logged_in_client("alice")
    note = create_note(client)
    assert client.patch(f"/notes/{note['id']}", json={"foo": "bar"}).status_code == 422


def test_patch_cannot_change_the_owner(logged_in_client):
    alice = logged_in_client("alice")
    bob = logged_in_client("bob")
    note = create_note(alice)
    alice.patch(f"/notes/{note['id']}", json={"user_id": 2, "title": "Still mine"})
    assert alice.get(f"/notes/{note['id']}").status_code == 200
    assert bob.get(f"/notes/{note['id']}").status_code == 403


def test_delete_note(logged_in_client):
    client = logged_in_client("alice")
    note = create_note(client)
    assert client.delete(f"/notes/{note['id']}").status_code == 204
    assert client.get(f"/notes/{note['id']}").status_code == 404


# ---------- access control ----------

def test_users_cannot_access_each_others_notes(logged_in_client):
    alice = logged_in_client("alice")
    bob = logged_in_client("bob")
    note = create_note(alice, title="Private")
    url = f"/notes/{note['id']}"

    assert bob.get(url).status_code == 403
    assert bob.patch(url, json={"title": "Hacked"}).status_code == 403
    assert bob.delete(url).status_code == 403

    still_there = alice.get(url).get_json()
    assert still_there["title"] == "Private"
