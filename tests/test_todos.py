"""
tests/test_todos.py

Covers GET, filtering, and basic CRUD for the /todos endpoint of the
JSONPlaceholder API (https://jsonplaceholder.typicode.com/todos).

The fixed dataset contains 200 todos distributed across 10 users (20 per user).
Each todo has a boolean `completed` field, making this endpoint the only place
in the API where boolean query parameter filtering can be tested.

CRUD coverage note: POST and PATCH are included here. PUT is intentionally
omitted — full PUT coverage including the missing-fields edge case lives in
test_posts.py. DELETE is omitted because the same 200+{} response shape is
already confirmed in test_posts.py and test_albums.py; repeating it here
adds no new information.
"""


# ---------------------------------------------------------------------------
# GET /todos
# ---------------------------------------------------------------------------

def test_get_all_todos_returns_200(session, base_url):
    # Baseline health check: confirms the endpoint is reachable before any
    # content or schema assertions are made.
    response = session.get(f"{base_url}/todos")
    assert response.status_code == 200


def test_get_all_todos_count(session, base_url):
    response = session.get(f"{base_url}/todos")
    # 10 users × 20 todos each = 200 total. Asserting the exact count confirms
    # the full collection is returned and the correct endpoint is being hit.
    assert len(response.json()) == 200


def test_todo_schema(session, base_url):
    response = session.get(f"{base_url}/todos")
    first = response.json()[0]
    # `completed` is the distinguishing field for this resource — it is the
    # only boolean field across the entire JSONPlaceholder API.
    assert {"id", "userId", "title", "completed"}.issubset(first.keys())


def test_todo_completed_is_boolean(session, base_url):
    response = session.get(f"{base_url}/todos")
    first = response.json()[0]
    # Explicitly asserting bool type rather than just truthiness. JSON booleans
    # (true/false) can be deserialized inconsistently across languages and
    # libraries — some return the string "true", the integer 1, or a truthy
    # object instead of a native boolean. A consumer doing `if todo["completed"]`
    # would not catch this; isinstance does. Catching "true" vs True here
    # prevents subtle bugs in any code that uses strict equality or type checks.
    assert isinstance(first["completed"], bool)


# ---------------------------------------------------------------------------
# GET /todos/{id}
# ---------------------------------------------------------------------------

def test_get_single_todo(session, base_url):
    response = session.get(f"{base_url}/todos/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_single_todo_invalid_id(session, base_url):
    # Negative path: consistent with the same test across all other resources
    # in the suite — non-existent ids should return 404.
    response = session.get(f"{base_url}/todos/9999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def test_filter_todos_completed_true(session, base_url):
    # The filter value is passed as the string "true" rather than Python's
    # boolean True because query parameters are always serialized as strings
    # in URLs. Passing True directly would be coerced to "True" (capital T)
    # by some HTTP libraries, which the API may not recognise.
    response = session.get(f"{base_url}/todos", params={"completed": "true"})
    assert response.status_code == 200
    todos = response.json()
    # Every item in the filtered result must have completed == True.
    # Iterating all items (not just the first) ensures the filter is applied
    # consistently across the full result set.
    assert all(todo["completed"] is True for todo in todos)


def test_filter_todos_completed_false(session, base_url):
    response = session.get(f"{base_url}/todos", params={"completed": "false"})
    assert response.status_code == 200
    todos = response.json()
    # Testing both boolean filter directions (True above, False here) confirms
    # the filter is doing real work — a filter that always returns all records
    # would pass the True-only test if the dataset happened to be all True.
    # Testing both states rules out a no-op filter.
    assert all(todo["completed"] is False for todo in todos)


def test_filter_todos_by_userid(session, base_url):
    response = session.get(f"{base_url}/todos", params={"userId": 1})
    assert response.status_code == 200
    todos = response.json()
    # Confirms the userId filter works on todos, consistent with the same
    # pattern on /posts and /albums. Every returned todo must belong to the
    # requested user — iterating all items rather than spot-checking one.
    assert all(todo["userId"] == 1 for todo in todos)


# ---------------------------------------------------------------------------
# CRUD (POST and PATCH only — see module docstring for omission rationale)
# ---------------------------------------------------------------------------

def test_create_todo(session, base_url):
    payload = {"userId": 1, "title": "Write test suite", "completed": False}
    response = session.post(f"{base_url}/todos", json=payload)
    # 201 Created is the correct status for a successful resource creation.
    assert response.status_code == 201


def test_patch_todo_completed(session, base_url):
    payload = {"completed": True}
    response = session.patch(f"{base_url}/todos/1", json=payload)
    assert response.status_code == 200
    # Use `is True` rather than a truthy check — the boolean type assertion
    # is consistent with test_todo_completed_is_boolean above. If the API
    # returned the string "true" or integer 1, `== True` would still pass
    # in some cases; `is True` is strict.
    assert response.json()["completed"] is True
