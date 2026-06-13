# JSONPlaceholder API Test Suite

API test suite targeting [JSONPlaceholder](https://jsonplaceholder.typicode.com), a purpose-built
fake REST API used for practicing and demonstrating API test automation. Built with Python, pytest,
and requests.

## What's Here

- 7 test files, 72 tests covering all 6 JSONPlaceholder resource endpoints and nested routes
- Session-scoped `requests.Session` fixture — one shared connection pool for the full test run, not one per test
- Schema validation, field type assertions, and boolean type checks across all resources
- Filtering tests for every resource that supports query parameters
- Documented API quirks: behaviors where JSONPlaceholder deviates from standard REST conventions, asserted and explained inline
- GitHub Actions CI workflow — full suite runs on every push and pull request to `main`

## Test Coverage

| File | Tests | What's Covered |
|------|-------|----------------|
| `tests/test_posts.py` | 20 | Full CRUD (GET, POST, PUT, PATCH, DELETE), schema and type validation, missing-field acceptance, filtering by userId, negative paths — canonical CRUD reference for the suite |
| `tests/test_comments.py` | 9 | GET all/single, schema, email format check, filtering by postId, POST, DELETE |
| `tests/test_albums.py` | 9 | GET all/single, schema, POST, PATCH, DELETE, filtering by userId |
| `tests/test_photos.py` | 7 | GET all (5000 items), schema, URL field non-empty assertions, GET single, filtering by albumId |
| `tests/test_todos.py` | 11 | GET all/single, boolean type assertion on `completed`, boolean filter (both true and false directions), filtering by userId, POST, PATCH |
| `tests/test_users.py` | 9 | GET all/single, deep nested schema validation (address → geo, company), email format |
| `tests/test_nested_routes.py` | 7 | Nested route correctness for all supported parent-child pairs, equivalence with query param filtering, invalid parent id behavior |

## API Findings

Several JSONPlaceholder behaviors deviate from standard REST conventions and are explicitly documented inline in the relevant test files:

- **DELETE on non-existent id returns 200** — `DELETE /posts/9999` returns 200, not 404. The API does not verify resource existence before acknowledging a delete.
- **Nested route with invalid parent returns 200 []** — `GET /posts/9999/comments` returns an empty list rather than 404. An empty list is ambiguous; the correct signal that the parent doesn't exist is 404.
- **POST accepts incomplete payloads** — Missing required fields (e.g. no `title` on a post) are accepted and echoed back with a 201. No server-side input validation is performed.
- **PUT accepts partial payloads** — A PUT body with only one field is accepted and echoed back rather than rejected with 400. Standard REST expects a full resource replacement on PUT.

These are documented as actual behavior, not bugs to fix — the suite asserts what the API does and explains what a stricter API would do differently.

## What's Not Here

- **No authentication tests** — JSONPlaceholder has no auth layer. There are no tokens, sessions, API keys, or protected routes to test.
- **No pagination tests** — The API returns complete collections on every request with no page size controls. The largest endpoint (`/photos`) returns all 5000 items in a single response.
- **No stateful sequence tests** — Write operations (POST, PUT, PATCH, DELETE) return realistic responses but do not persist. A created resource cannot be retrieved in a subsequent GET, so create-then-verify sequences are not meaningful.
- **No rate limiting or performance tests** — The API imposes no request throttling. There is no server behavior to probe for latency, timeouts, or concurrency limits.
- **No cross-resource write sequences** — Creating a user and then creating posts for that user would require persistence. Since the API is stateless, these flows have no real surface area.

## Tech Stack

- Python 3.13
- [pytest](https://docs.pytest.org/) — test framework and runner
- [requests](https://requests.readthedocs.io/) — HTTP client

## Setup

```bash
pip install -r requirements.txt
```

## Running Tests

```bash
# Run the full suite
pytest

# Run a single test file
pytest tests/test_posts.py

# Run with verbose output
pytest -v

# Run a single test by name
pytest tests/test_posts.py::test_create_post_status
```

## CI (GitHub Actions)

The workflow in `.github/workflows/pytest.yml` runs the full suite on every push to `main` and on pull requests. No secrets or credentials are required — the suite targets the public JSONPlaceholder API.

## A Note on AI-Assisted Development

The test strategy, coverage decisions, and quality bar in this suite are mine. I
used Claude Code to speed up implementation, the same way I'd use any tool in a
modern workflow — directing it, reviewing its output, and rejecting what didn't
meet the bar. Knowing what to test, how to verify it, and when to push back is the
work; the tooling just makes it faster.
