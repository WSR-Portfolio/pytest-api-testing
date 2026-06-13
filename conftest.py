import pytest
import requests


# Session scope means this fixture is created once for the entire test run and
# shared across all test files. The base URL is a single source of truth —
# changing the target environment (e.g. staging vs production) requires editing
# one line rather than hunting down hardcoded strings across every test file.
@pytest.fixture(scope="session")
def base_url():
    """Base URL for the JSONPlaceholder API, shared across the entire test session."""
    return "https://jsonplaceholder.typicode.com"


# Session scope keeps one requests.Session alive for the full test run instead
# of creating and tearing down a connection per test. Benefits:
#   - Reuses the underlying TCP connection pool, reducing per-request latency
#   - Applies shared headers (Content-Type) once rather than in every test
#   - Lowers unnecessary load on the target server during a suite run
# yield is used instead of return so s.close() runs as teardown after all tests
# finish, cleanly releasing the connection pool rather than relying on GC.
@pytest.fixture(scope="session")
def session():
    """
    Shared requests.Session for the full test run.

    Pre-sets Content-Type: application/json on all requests. Uses yield so
    the session is explicitly closed after the suite completes rather than
    relying on garbage collection to release the connection pool.
    """
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    yield s
    s.close()


# Centralised in conftest so every test file can consume this fixture without
# duplicating the payload definition. Keeping it here also makes it the
# canonical example of a valid post body, so tests that need a known-good
# payload stay in sync automatically.
# Function scope (the default, stated explicitly for clarity) gives each test
# its own fresh dict copy — mutations made by one test cannot leak state into
# the next, which would produce order-dependent failures that are hard to debug.
@pytest.fixture(scope="function")
def valid_post_payload():
    """
    A known-good POST payload for the /posts endpoint.

    Function-scoped so each test receives an independent dict copy — mutations
    in one test cannot leak state into the next.
    """
    return {
        "userId": 1,
        "title": "Test Post Title",
        "body": "This is the body of the test post.",
    }
