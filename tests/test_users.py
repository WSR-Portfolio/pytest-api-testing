"""
tests/test_users.py

Covers GET and deep schema validation for the /users endpoint of the
JSONPlaceholder API (https://jsonplaceholder.typicode.com/users).

Focus on read operations and schema depth rather than full CRUD: the user
resource has only 10 records and is the root owner of posts, albums, and todos.
CRUD patterns are covered thoroughly in test_posts.py. The more meaningful
test surface here is the nested schema — users are the most structurally
complex resource in the API, with address and company objects that each contain
their own nested fields. Shallow GET tests on a resource with 10 items would
add little value; verifying the full shape of the response does.

Filter tests are omitted: JSONPlaceholder does not expose a meaningful query
parameter filter for users. Unlike posts, albums, todos, and comments — which
all support filtering by userId or a parent id — there is no parent resource
above users and no documented filter parameter for the /users collection.
User-scoped filtering is tested via nested routes in test_nested_routes.py
(e.g. /users/1/posts).
"""


# ---------------------------------------------------------------------------
# GET /users
# ---------------------------------------------------------------------------

def test_get_all_users_returns_200(session, base_url):
    # Baseline health check: confirms the endpoint is reachable before any
    # content or schema assertions are made.
    response = session.get(f"{base_url}/users")
    assert response.status_code == 200


def test_get_all_users_count(session, base_url):
    response = session.get(f"{base_url}/users")
    # The fixed dataset has exactly 10 users. Every other resource in the API
    # (posts, albums, todos, comments, photos) traces ownership back to one of
    # these 10 records via userId.
    assert len(response.json()) == 10


# ---------------------------------------------------------------------------
# Schema validation (top-level and nested)
# ---------------------------------------------------------------------------

def test_user_top_level_schema(session, base_url):
    response = session.get(f"{base_url}/users")
    first = response.json()[0]
    # The user resource has the most complex schema in this API — 8 top-level
    # fields including two nested objects (address, company). Validating all
    # top-level keys here establishes the baseline before descending into
    # nested structure in the tests below.
    assert {"id", "name", "username", "email", "phone", "website", "address", "company"}.issubset(first.keys())


def test_user_address_schema(session, base_url):
    response = session.get(f"{base_url}/users")
    address = response.json()[0]["address"]
    # Nested object validation confirms the API is returning fully-formed data
    # structures, not just top-level fields with empty or null nested values.
    # A schema check on the parent object alone would not catch a response
    # where address is present but contains only one or two fields.
    assert {"street", "city", "zipcode", "geo"}.issubset(address.keys())


def test_user_geo_schema(session, base_url):
    response = session.get(f"{base_url}/users")
    geo = response.json()[0]["address"]["geo"]
    # One level deeper into the nested structure. Confirms the full depth of
    # the address object is populated — geo could be present as an empty object
    # {} and the parent address test would still pass. lat and lng are the
    # fields a mapping consumer would actually need.
    assert {"lat", "lng"}.issubset(geo.keys())


def test_user_company_schema(session, base_url):
    response = session.get(f"{base_url}/users")
    company = response.json()[0]["company"]
    # company is a sibling nested object to address. Validating it separately
    # keeps failures isolated — a missing company field produces a clear error
    # pointing here rather than a combined assertion failure.
    assert {"name", "catchPhrase", "bs"}.issubset(company.keys())


def test_user_email_format(session, base_url):
    response = session.get(f"{base_url}/users")
    email = response.json()[0]["email"]
    # Lightweight format check — the same approach used in test_comments.py
    # for the same reason: plausibility over strict compliance. Verifies the
    # field contains email-shaped data rather than an empty string or a value
    # from a misrouted field, without pulling in an extra validation library.
    assert "@" in email
    assert "." in email


# ---------------------------------------------------------------------------
# GET /users/{id}
# ---------------------------------------------------------------------------

def test_get_single_user(session, base_url):
    response = session.get(f"{base_url}/users/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_single_user_invalid_id(session, base_url):
    # Negative path: consistent with the same test across all other resources.
    # With only 10 users in the dataset, 9999 is safely outside the valid range.
    response = session.get(f"{base_url}/users/9999")
    assert response.status_code == 404
