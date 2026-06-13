"""
tests/test_photos.py

Covers GET and filtering for the /photos endpoint of the JSONPlaceholder API
(https://jsonplaceholder.typicode.com/photos).

Note on CRUD coverage: full POST/PUT/PATCH/DELETE tests are intentionally
omitted here. All HTTP verbs are exercised thoroughly in test_posts.py, which
is the canonical place for CRUD pattern coverage in this suite. Photos are
structurally simple (five scalar fields) and adding identical CRUD tests for
every resource would inflate test count without adding meaningful coverage —
each additional resource-level CRUD block would be testing the test framework's
ability to make HTTP calls, not any new API behavior.
"""


# ---------------------------------------------------------------------------
# GET /photos
# ---------------------------------------------------------------------------

def test_get_all_photos_returns_200(session, base_url):
    response = session.get(f"{base_url}/photos")
    assert response.status_code == 200


def test_get_all_photos_count(session, base_url):
    response = session.get(f"{base_url}/photos")
    # 5000 items: 100 albums × 50 photos each. This is the largest collection
    # in the JSONPlaceholder API by an order of magnitude — the next largest
    # is /comments at 500. Asserting the exact count ensures the full dataset
    # is returned and guards against accidentally hitting a paginated or
    # truncated response.
    assert len(response.json()) == 5000


def test_photo_schema(session, base_url):
    response = session.get(f"{base_url}/photos")
    first = response.json()[0]
    # Photos carry two URL fields (full-size and thumbnail) in addition to the
    # standard id/albumId/title triple. Both must be present for the resource
    # to be useful to a consumer rendering images.
    assert {"id", "albumId", "title", "url", "thumbnailUrl"}.issubset(first.keys())


def test_photo_url_fields_are_strings(session, base_url):
    response = session.get(f"{base_url}/photos")
    first = response.json()[0]
    # Schema presence (tested above) only confirms the keys exist — a field
    # can be present but null, empty, or the wrong type. Asserting non-empty
    # strings here verifies the URL fields contain usable data, which is the
    # minimum a consumer needs before attempting to fetch or display an image.
    assert isinstance(first["url"], str) and len(first["url"]) > 0
    assert isinstance(first["thumbnailUrl"], str) and len(first["thumbnailUrl"]) > 0


# ---------------------------------------------------------------------------
# GET /photos/{id}
# ---------------------------------------------------------------------------

def test_get_single_photo(session, base_url):
    response = session.get(f"{base_url}/photos/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_single_photo_invalid_id(session, base_url):
    # Non-existent id should return 404, consistent with the same negative-path
    # test across /posts, /comments, and /albums.
    response = session.get(f"{base_url}/photos/9999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def test_filter_photos_by_albumid(session, base_url):
    response = session.get(f"{base_url}/photos", params={"albumId": 1})
    assert response.status_code == 200
    photos = response.json()
    # Every photo in the filtered result must belong to the requested album.
    # Iterating all items (rather than spot-checking one) ensures the filter
    # is applied uniformly across the full result set.
    assert all(photo["albumId"] == 1 for photo in photos)
