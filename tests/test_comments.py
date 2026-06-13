"""
tests/test_comments.py

Covers GET, filtering, field validation, and basic CRUD for the /comments
endpoint of the JSONPlaceholder API (https://jsonplaceholder.typicode.com/comments).

Comments are nested under posts (each post has 5 comments in the fixed dataset,
yielding 500 total across 100 posts). Write operations do not persist state.

CRUD coverage note: POST and DELETE are included here to confirm the endpoint
accepts writes. PUT and PATCH are intentionally omitted — full verb coverage
including edge cases (missing fields, partial payloads, response shape) lives
in test_posts.py, which is the canonical CRUD reference for this suite.
Repeating those patterns here would add test count without adding coverage value.
"""


# ---------------------------------------------------------------------------
# GET /comments
# ---------------------------------------------------------------------------

def test_get_all_comments_returns_200(session, base_url):
    # Baseline health check: confirms the endpoint is reachable before any
    # content or schema assertions are made.
    response = session.get(f"{base_url}/comments")
    assert response.status_code == 200


def test_get_all_comments_count(session, base_url):
    response = session.get(f"{base_url}/comments")
    # The fixed dataset has 100 posts × 5 comments each = 500 comments total.
    # Asserting the exact count verifies the full collection is returned and
    # the correct endpoint is being hit.
    assert len(response.json()) == 500


def test_comment_schema(session, base_url):
    response = session.get(f"{base_url}/comments")
    first = response.json()[0]
    # postId links the comment back to its parent post. Confirming all five
    # keys are present validates the full contract for a comment object.
    assert {"id", "postId", "name", "email", "body"}.issubset(first.keys())


# ---------------------------------------------------------------------------
# GET /comments/{id}
# ---------------------------------------------------------------------------

def test_get_single_comment(session, base_url):
    response = session.get(f"{base_url}/comments/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_single_comment_invalid_id(session, base_url):
    # Confirms the API returns 404 for a non-existent id rather than an empty
    # object or a 500 error. Mirrors the same negative-path test on /posts.
    response = session.get(f"{base_url}/comments/9999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Field validation
# ---------------------------------------------------------------------------

def test_comment_email_format(session, base_url):
    response = session.get(f"{base_url}/comments/1")
    email = response.json()["email"]
    # A lightweight format check: asserting "@" and "." are present confirms
    # the field contains plausible email-shaped data rather than an empty
    # string, a placeholder, or a misrouted field value. A full RFC 5322
    # regex or a library like `email-validator` would be appropriate for a
    # production system, but here the goal is data plausibility, not strict
    # compliance — and pulling in an extra dependency for one assertion would
    # be disproportionate given the fake-API context.
    assert "@" in email
    assert "." in email


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def test_filter_comments_by_postid(session, base_url):
    response = session.get(f"{base_url}/comments", params={"postId": 1})
    assert response.status_code == 200
    comments = response.json()
    # Every comment in the filtered result must belong to the requested post.
    # Checking all items (not just the first) ensures the filter is applied
    # to the full result set and not just the ordering of results.
    assert all(comment["postId"] == 1 for comment in comments)


# ---------------------------------------------------------------------------
# CRUD (POST and DELETE only — see module docstring for omission rationale)
# ---------------------------------------------------------------------------

def test_create_comment(session, base_url):
    payload = {
        "postId": 1,
        "name": "Test Commenter",
        "email": "test@example.com",
        "body": "This is a test comment body.",
    }
    response = session.post(f"{base_url}/comments", json=payload)
    # 201 Created is the correct status for a successful resource creation.
    assert response.status_code == 201


def test_delete_comment(session, base_url):
    response = session.delete(f"{base_url}/comments/1")
    # JSONPlaceholder acknowledges the delete with 200 and an empty JSON
    # object. State is not actually mutated — subsequent GETs still return
    # the comment — but the response code and shape are consistent.
    assert response.status_code == 200
