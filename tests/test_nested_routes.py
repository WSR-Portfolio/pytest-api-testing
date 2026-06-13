"""
tests/test_nested_routes.py

Tests nested resource routes on the JSONPlaceholder API
(https://jsonplaceholder.typicode.com).

Nested routes expose parent-child relationships between resources using URL
structure rather than query parameters — e.g. /posts/1/comments instead of
/comments?postId=1. JSONPlaceholder supports one level of nesting, meaning
you can reach a child collection through its parent but cannot chain further
(e.g. /users/1/posts/1/comments is not supported).

These routes are documented as functionally equivalent to query parameter
filtering on the child resource. One test below verifies that equivalence
explicitly for the posts/comments pair, because "documented as equivalent"
and "actually equivalent" are not the same thing in all API implementations.
The equivalence check is not repeated for every route pair — once the pattern
is confirmed for one pair, the remaining routes are tested for correctness
(right parent id in every result) rather than equivalence, which would be
redundant given they share the same underlying implementation.

Routes not present in this file:
- /users/:id/comments: users do not directly own comments in this API.
  Comments belong to posts, which belong to users. There is no direct
  /users/:id/comments route — only /posts/:id/comments.
- /posts/:id/photos, /albums/:id/comments, etc.: JSONPlaceholder only exposes
  parent-child routes for the relationships that exist in its data model.
  Untested combinations return 404 or an empty list and are not meaningful
  to test here.
"""


def test_posts_comments_nested_route(session, base_url):
    response = session.get(f"{base_url}/posts/1/comments")
    assert response.status_code == 200
    comments = response.json()
    # Verify the route returns only comments belonging to the specified post,
    # not the full /comments collection or comments from other posts.
    assert all(comment["postId"] == 1 for comment in comments)


def test_nested_route_matches_query_param(session, base_url):
    nested = session.get(f"{base_url}/posts/1/comments")
    filtered = session.get(f"{base_url}/comments", params={"postId": 1})

    nested_ids = {c["id"] for c in nested.json()}
    filtered_ids = {c["id"] for c in filtered.json()}

    # Verifies that the nested route and the query parameter filter are truly
    # equivalent — same count and identical set of resource ids. APIs sometimes
    # implement these paths independently, which can lead to subtle drift: one
    # path may include soft-deleted records, apply different pagination defaults,
    # or use a different sort order. Asserting on id sets rather than full
    # objects keeps this check focused on membership, not field-level response
    # shape. This test is only run for one route pair (posts/comments) because
    # the equivalence property is an implementation characteristic of the whole
    # API, not something that needs to be re-proven per resource.
    assert len(nested_ids) == len(filtered_ids)
    assert nested_ids == filtered_ids


def test_albums_photos_nested_route(session, base_url):
    response = session.get(f"{base_url}/albums/1/photos")
    assert response.status_code == 200
    photos = response.json()
    # Confirms the albums→photos relationship is correctly scoped: only photos
    # belonging to album 1 are returned, not photos from other albums.
    assert all(photo["albumId"] == 1 for photo in photos)


def test_users_posts_nested_route(session, base_url):
    response = session.get(f"{base_url}/users/1/posts")
    assert response.status_code == 200
    posts = response.json()
    # Confirms the users→posts relationship is correctly scoped. This is the
    # primary ownership chain in the API: users own posts, posts own comments.
    assert all(post["userId"] == 1 for post in posts)


def test_users_todos_nested_route(session, base_url):
    response = session.get(f"{base_url}/users/1/todos")
    assert response.status_code == 200
    todos = response.json()
    # Confirms the users→todos relationship is correctly scoped. Todos are
    # owned directly by users (not through an intermediate resource).
    assert all(todo["userId"] == 1 for todo in todos)


def test_users_albums_nested_route(session, base_url):
    response = session.get(f"{base_url}/users/1/albums")
    assert response.status_code == 200
    albums = response.json()
    # Confirms the users→albums relationship is correctly scoped. Albums are
    # owned directly by users; photos are then owned by albums (one level deeper).
    assert all(album["userId"] == 1 for album in albums)


def test_nested_route_invalid_parent_id(session, base_url):
    response = session.get(f"{base_url}/posts/9999/comments")
    # JSONPlaceholder returns 200 with an empty list [] when the parent id does
    # not exist, rather than 404. This is the same quirk observed with DELETE
    # on non-existent resources — the API does not validate parent existence
    # before resolving the child route. The correct REST behavior would be 404,
    # because an empty list is ambiguous: it could mean the parent exists with
    # no children, or the parent does not exist at all. The assertion documents
    # actual API behavior so the test does not misrepresent correct semantics.
    assert response.status_code == 200
    assert response.json() == []
