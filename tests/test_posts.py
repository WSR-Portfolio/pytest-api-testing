"""
tests/test_posts.py

Covers CRUD operations and filtering for the /posts endpoint of the
JSONPlaceholder API (https://jsonplaceholder.typicode.com/posts).

This is the canonical CRUD file for the suite. POST, PUT, PATCH, and DELETE
are exercised in full here — including edge cases like missing fields and
non-existent ids — so that other resource files (albums, comments, todos, etc.)
can defer to this file rather than repeating the same verb-level patterns.

JSONPlaceholder is a read-only fake REST API. Write operations (POST, PUT,
PATCH, DELETE) return realistic responses but do not mutate server state —
each test run starts from the same fixed dataset. Tests that assert on
specific field values (e.g. userId == 1 for /posts/1) are safe to rely on
because the dataset never changes.
"""


# ---------------------------------------------------------------------------
# GET /posts
# ---------------------------------------------------------------------------

def test_get_all_posts_returns_200(session, base_url):
    # Baseline health check: confirms the endpoint is reachable and the server
    # is responding before any content or schema assertions are made.
    response = session.get(f"{base_url}/posts")
    assert response.status_code == 200


def test_get_all_posts_returns_list(session, base_url):
    response = session.get(f"{base_url}/posts")
    # The endpoint should return a JSON array, not a JSON object.
    # A dict response would indicate a wrapping envelope or error body.
    assert isinstance(response.json(), list)


def test_get_all_posts_count(session, base_url):
    response = session.get(f"{base_url}/posts")
    # The fixed dataset contains exactly 100 posts across 10 users.
    # Asserting the count catches regressions if the base URL or path
    # is wrong and a different resource is returned instead.
    assert len(response.json()) == 100


def test_post_schema(session, base_url):
    response = session.get(f"{base_url}/posts")
    first = response.json()[0]
    # Validate the expected contract for a post object. Checking keys rather
    # than exact values here so the test stays valid even if upstream data
    # were ever reordered.
    assert {"id", "userId", "title", "body"}.issubset(first.keys())


def test_post_field_types(session, base_url):
    response = session.get(f"{base_url}/posts")
    first = response.json()[0]
    # Type assertions catch serialisation bugs (e.g. id returned as "1"
    # instead of 1) that would break any consumer doing arithmetic or
    # strict equality checks on these fields.
    assert isinstance(first["id"], int)
    assert isinstance(first["userId"], int)
    assert isinstance(first["title"], str)
    assert isinstance(first["body"], str)


# ---------------------------------------------------------------------------
# GET /posts/{id}
# ---------------------------------------------------------------------------

def test_get_single_post(session, base_url):
    response = session.get(f"{base_url}/posts/1")
    assert response.status_code == 200
    # Confirm the API returned the resource we asked for, not a default or
    # fallback record.
    assert response.json()["id"] == 1


def test_get_single_post_invalid_id(session, base_url):
    # Negative path: an id that does not exist in the dataset should return
    # 404, not 200 with an empty body or a server error. Testing this
    # confirms the API distinguishes "not found" from "bad request".
    response = session.get(f"{base_url}/posts/9999")
    assert response.status_code == 404


def test_get_single_post_userid_value(session, base_url):
    response = session.get(f"{base_url}/posts/1")
    # Anchoring against a known value from the fixed dataset. Post id=1
    # belongs to userId=1 in JSONPlaceholder's seed data. This catches
    # routing bugs where the wrong record is returned for a given id.
    assert response.json()["userId"] == 1


# ---------------------------------------------------------------------------
# POST /posts
# ---------------------------------------------------------------------------

def test_create_post_status(session, base_url, valid_post_payload):
    response = session.post(f"{base_url}/posts", json=valid_post_payload)
    # REST convention: a successful resource creation returns 201 Created,
    # not 200 OK. Asserting 201 verifies the API follows this convention.
    assert response.status_code == 201


def test_create_post_response_content_type(session, base_url, valid_post_payload):
    response = session.post(f"{base_url}/posts", json=valid_post_payload)
    # Use `in` rather than equality because Content-Type often includes a
    # charset suffix (e.g. "application/json; charset=utf-8").
    assert "application/json" in response.headers["Content-Type"]


def test_create_post_missing_field(session, base_url):
    # JSONPlaceholder does not validate request payloads — it accepts and
    # echoes back whatever is sent, including incomplete bodies. This is
    # documented API behavior, not a bug. The test is explicitly included
    # (rather than skipped) to record this contract: callers cannot rely on
    # the API to reject malformed input, so validation must live client-side.
    payload = {"userId": 1, "body": "No title provided"}
    response = session.post(f"{base_url}/posts", json=payload)
    assert response.status_code == 201


# ---------------------------------------------------------------------------
# PUT /posts/{id}
# ---------------------------------------------------------------------------

def test_put_post(session, base_url):
    payload = {
        "id": 1,
        "userId": 1,
        "title": "Updated Title",
        "body": "Updated body content.",
    }
    response = session.put(f"{base_url}/posts/1", json=payload)
    assert response.status_code == 200
    # Verify the response reflects the submitted data, not the original record.
    assert response.json()["title"] == "Updated Title"


def test_put_post_missing_fields(session, base_url):
    # JSONPlaceholder does not enforce required fields on PUT. A partial
    # payload is accepted and echoed back as if it were a full replacement.
    # This documents actual API behavior — a stricter API would return 400
    # here. Callers should not infer from this that partial PUT is valid REST.
    payload = {"userId": 1}
    response = session.put(f"{base_url}/posts/1", json=payload)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# PATCH /posts/{id}
# ---------------------------------------------------------------------------

def test_patch_post_title(session, base_url):
    payload = {"title": "Patched Title"}
    response = session.patch(f"{base_url}/posts/1", json=payload)
    assert response.status_code == 200
    assert response.json()["title"] == "Patched Title"


def test_patch_preserves_other_fields(session, base_url):
    # PATCH semantics: only the specified fields are modified; all other
    # fields on the resource should remain present and unchanged. This is
    # the key distinction from PUT, which replaces the entire resource.
    # Asserting key presence (not value) is sufficient here because
    # JSONPlaceholder does not persist state between requests.
    payload = {"title": "Patched Title Only"}
    response = session.patch(f"{base_url}/posts/1", json=payload)
    body = response.json()
    assert "userId" in body
    assert "body" in body


# ---------------------------------------------------------------------------
# DELETE /posts/{id}
# ---------------------------------------------------------------------------

def test_delete_post(session, base_url):
    # Confirms the delete verb is accepted and returns a success code.
    # Response body shape is asserted separately in test_delete_post_response_body
    # so a failure isolates whether the issue is the status code or the body.
    response = session.delete(f"{base_url}/posts/1")
    assert response.status_code == 200


def test_delete_post_response_body(session, base_url):
    response = session.delete(f"{base_url}/posts/1")
    # JSONPlaceholder returns an empty JSON object {} on successful delete.
    # Asserting this confirms the response is valid JSON and has the expected
    # shape — some APIs return 204 No Content with no body instead.
    assert response.json() == {}


def test_delete_nonexistent_post(session, base_url):
    # JSONPlaceholder returns 200 for DELETE on a non-existent id rather than
    # 404. This is a known quirk of the fake API — it does not check whether
    # the resource exists before acknowledging the delete. A production API
    # would return 404 here. The assertion documents actual behavior so the
    # test doesn't give a false impression of correct REST semantics.
    response = session.delete(f"{base_url}/posts/9999")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def test_filter_posts_by_userid(session, base_url):
    response = session.get(f"{base_url}/posts", params={"userId": 1})
    assert response.status_code == 200
    posts = response.json()
    # Every post in the filtered result must belong to the requested user.
    # Iterating all items (rather than spot-checking one) ensures the API
    # isn't leaking records from other users.
    assert all(post["userId"] == 1 for post in posts)


def test_filter_posts_by_userid_count(session, base_url):
    response = session.get(f"{base_url}/posts", params={"userId": 1})
    posts = response.json()
    # The fixed dataset assigns exactly 10 posts to each of 10 users (100
    # total). Asserting the count here verifies the filter is working and
    # not returning the full unfiltered list.
    assert len(posts) == 10
