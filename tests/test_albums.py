"""
tests/test_albums.py

Covers GET, CRUD, and filtering for the /albums endpoint of the JSONPlaceholder
API (https://jsonplaceholder.typicode.com/albums).

The fixed dataset contains 100 albums distributed evenly across 10 users (10
albums per user). Write operations return realistic responses but do not persist
state — the dataset resets between test runs automatically.

CRUD coverage note: POST, PATCH, and DELETE are included here. PUT is
intentionally omitted — PUT coverage including the missing-fields edge case
is in test_posts.py, which is the canonical CRUD reference for this suite.
Albums have the same three-field schema (id, userId, title) as the PUT payload
shape, so there is no new behavior to exercise that test_posts.py does not
already cover.
"""


# ---------------------------------------------------------------------------
# GET /albums
# ---------------------------------------------------------------------------

def test_get_all_albums_returns_200(session, base_url):
    # Baseline health check: confirms the endpoint is reachable before any
    # content or schema assertions are made.
    response = session.get(f"{base_url}/albums")
    assert response.status_code == 200


def test_get_all_albums_count(session, base_url):
    response = session.get(f"{base_url}/albums")
    # 10 users × 10 albums each = 100 total. Asserting the exact count
    # verifies the full collection is returned and the correct path is hit.
    assert len(response.json()) == 100


def test_album_schema(session, base_url):
    response = session.get(f"{base_url}/albums")
    first = response.json()[0]
    # Albums have a simpler schema than posts or comments — three fields only.
    # userId links the album to its owner; title is the only descriptive field.
    assert {"id", "userId", "title"}.issubset(first.keys())


# ---------------------------------------------------------------------------
# GET /albums/{id}
# ---------------------------------------------------------------------------

def test_get_single_album(session, base_url):
    response = session.get(f"{base_url}/albums/1")
    assert response.status_code == 200
    # Confirm the response contains the requested resource, not a default or
    # fallback record.
    assert response.json()["id"] == 1


def test_get_single_album_invalid_id(session, base_url):
    # Negative path: a non-existent id should return 404, not an empty object
    # or a 500. Consistent with the same test pattern across /posts and /comments.
    response = session.get(f"{base_url}/albums/9999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# CRUD (POST, PATCH, DELETE only — see module docstring for PUT omission rationale)
# ---------------------------------------------------------------------------

def test_create_album(session, base_url):
    payload = {"userId": 1, "title": "Test Album"}
    response = session.post(f"{base_url}/albums", json=payload)
    # 201 Created is the correct status for a successful resource creation.
    assert response.status_code == 201


def test_patch_album_title(session, base_url):
    payload = {"title": "Patched Album Title"}
    response = session.patch(f"{base_url}/albums/1", json=payload)
    assert response.status_code == 200
    # Verify the response echoes the patched value. Only the title is sent —
    # PATCH semantics mean other fields (userId, id) should remain present
    # in the response, unaffected by the partial update.
    assert response.json()["title"] == "Patched Album Title"


def test_delete_album(session, base_url):
    response = session.delete(f"{base_url}/albums/1")
    # JSONPlaceholder returns 200 with an empty JSON object on delete.
    # State is not actually mutated — the album is still retrievable via GET —
    # but the response code confirms the API acknowledged the request correctly.
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def test_filter_albums_by_userid(session, base_url):
    response = session.get(f"{base_url}/albums", params={"userId": 1})
    assert response.status_code == 200
    albums = response.json()
    # Every album in the filtered result must belong to the requested user.
    # Iterating all items ensures the filter is applied to the full result
    # set, not just the leading records.
    assert all(album["userId"] == 1 for album in albums)
