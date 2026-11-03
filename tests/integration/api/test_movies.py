import os
from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from moviely.db.session import get_engine, get_session
from moviely.main import app

pytestmark = pytest.mark.skipif(
    os.getenv("MOVIELY_TEST_POSTGRES") != "1",
    reason="Requires PostgreSQL integration environment",
)


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = get_engine()

    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as session:

                def override_get_session() -> Iterator[Session]:
                    yield session

                app.dependency_overrides[get_session] = override_get_session

                try:
                    with TestClient(app) as test_client:
                        yield test_client
                finally:
                    app.dependency_overrides.pop(get_session, None)
        finally:
            transaction.rollback()


def test_create_movie(client: TestClient) -> None:
    response = client.post(
        "/movies",
        json={
            "title": "Interstellar",
            "runtime_minutes": 169,
            "status": "released",
        },
    )

    assert response.status_code == 201

    movie = response.json()

    assert movie["title"] == "Interstellar"
    assert movie["runtime_minutes"] == 169
    assert movie["status"] == "released"
    assert movie["id"]
    assert movie["created_at"]
    assert movie["updated_at"]


def test_get_movie(client: TestClient) -> None:
    created = client.post(
        "/movies",
        json={"title": "Get Movie Test"},
    ).json()

    response = client.get(f"/movies/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["title"] == "Get Movie Test"


def test_get_missing_movie(client: TestClient) -> None:
    response = client.get(f"/movies/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Movie not found"


def test_create_rejects_invalid_title(client: TestClient) -> None:
    response = client.post(
        "/movies",
        json={"title": "   "},
    )

    assert response.status_code == 422


def test_list_movies(client: TestClient) -> None:
    first = client.post(
        "/movies",
        json={"title": "First API Movie"},
    ).json()

    second = client.post(
        "/movies",
        json={"title": "Second API Movie"},
    ).json()

    response = client.get("/movies?limit=20&offset=0")

    assert response.status_code == 200

    movie_ids = {movie["id"] for movie in response.json()}

    assert first["id"] in movie_ids
    assert second["id"] in movie_ids


@pytest.mark.parametrize(
    "query",
    ["limit=0", "limit=101", "offset=-1"],
)
def test_list_rejects_invalid_pagination(
    client: TestClient,
    query: str,
) -> None:
    response = client.get(f"/movies?{query}")

    assert response.status_code == 422


def test_replace_movie(client: TestClient) -> None:
    created = client.post(
        "/movies",
        json={
            "title": "Original Movie",
            "overview": "Original overview",
            "runtime_minutes": 120,
            "status": "released",
        },
    ).json()

    response = client.put(
        f"/movies/{created['id']}",
        json={"title": "Replacement Movie"},
    )

    assert response.status_code == 200

    movie = response.json()

    assert movie["id"] == created["id"]
    assert movie["title"] == "Replacement Movie"
    assert movie["overview"] is None
    assert movie["runtime_minutes"] is None
    assert movie["status"] == "announced"


def test_patch_movie_preserves_omitted_fields(client: TestClient) -> None:
    created = client.post(
        "/movies",
        json={
            "title": "Original Movie",
            "overview": "Keep this overview",
            "runtime_minutes": 120,
        },
    ).json()

    response = client.patch(
        f"/movies/{created['id']}",
        json={"title": "Updated Movie"},
    )

    assert response.status_code == 200

    movie = response.json()

    assert movie["title"] == "Updated Movie"
    assert movie["overview"] == "Keep this overview"
    assert movie["runtime_minutes"] == 120


def test_patch_movie_clears_nullable_field(client: TestClient) -> None:
    created = client.post(
        "/movies",
        json={
            "title": "Original Movie",
            "overview": "Remove this",
        },
    ).json()

    response = client.patch(
        f"/movies/{created['id']}",
        json={"overview": None},
    )

    assert response.status_code == 200
    assert response.json()["overview"] is None


def test_empty_patch_preserves_movie(client: TestClient) -> None:
    created = client.post(
        "/movies",
        json={"title": "Unchanged Movie"},
    ).json()

    response = client.patch(
        f"/movies/{created['id']}",
        json={},
    )

    assert response.status_code == 200
    assert response.json()["title"] == created["title"]
    assert response.json()["updated_at"] == created["updated_at"]


def test_delete_movie(client: TestClient) -> None:
    created = client.post(
        "/movies",
        json={"title": "Delete Me"},
    ).json()

    movie_id = created["id"]

    response = client.delete(f"/movies/{movie_id}")

    assert response.status_code == 204
    assert response.content == b""

    get_response = client.get(f"/movies/{movie_id}")

    assert get_response.status_code == 404


def test_head_existing_movie(client: TestClient) -> None:
    created = client.post(
        "/movies",
        json={"title": "HEAD Test"},
    ).json()

    response = client.head(f"/movies/{created['id']}")

    assert response.status_code == 200
    assert response.content == b""


def test_head_missing_movie(client: TestClient) -> None:
    response = client.head(f"/movies/{uuid4()}")

    assert response.status_code == 404
    assert response.content == b""


@pytest.mark.parametrize(
    "method,payload",
    [
        ("put", {"title": "Replacement"}),
        ("patch", {"title": "Updated"}),
        ("delete", None),
    ],
)
def test_missing_movie_returns_404(
    client: TestClient,
    method: str,
    payload: dict[str, str] | None,
) -> None:
    movie_id = uuid4()

    response = client.request(
        method.upper(),
        f"/movies/{movie_id}",
        json=payload,
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": None},
        {"title": ""},
        {"title": "   "},
        {"title": "A" * 256},
        {"title": "Movie", "runtime_minutes": 0},
        {"title": "Movie", "runtime_minutes": -10},
        {"title": "Movie", "status": "invalid"},
        {"title": "Movie", "original_language": "x" * 11},
    ],
)
def test_create_rejects_invalid_payload(
    client: TestClient,
    payload: dict,
) -> None:
    response = client.post("/movies", json=payload)

    assert response.status_code == 422


def test_get_rejects_invalid_uuid(client: TestClient) -> None:
    response = client.get("/movies/not-a-uuid")

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": None},
        {"title": "   "},
        {"title": "Movie", "status": None},
    ],
)
def test_replace_rejects_invalid_payload(
    client: TestClient,
    payload: dict,
) -> None:
    created = client.post(
        "/movies",
        json={"title": "Original Movie"},
    ).json()

    response = client.put(
        f"/movies/{created['id']}",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"title": None},
        {"title": "   "},
        {"status": None},
        {"status": "invalid"},
        {"runtime_minutes": 0},
    ],
)
def test_patch_rejects_invalid_payload(
    client: TestClient,
    payload: dict,
) -> None:
    created = client.post(
        "/movies",
        json={"title": "Original Movie"},
    ).json()

    response = client.patch(
        f"/movies/{created['id']}",
        json=payload,
    )

    assert response.status_code == 422

    # Invalid requests must not alter the existing Movie.
    retrieved = client.get(f"/movies/{created['id']}")

    assert retrieved.status_code == 200
    assert retrieved.json()["title"] == "Original Movie"


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "Movie", "unknown_field": "unexpected"},
        {"title": "Movie", "id": str(uuid4())},
        {"title": "Movie", "created_at": "2026-01-01T00:00:00Z"},
        {"title": "Movie", "updated_at": "2026-01-01T00:00:00Z"},
    ],
)
def test_create_rejects_unknown_or_readonly_fields(
    client: TestClient,
    payload: dict,
) -> None:
    response = client.post("/movies", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "method,payload",
    [
        ("put", {"title": "Replacement", "id": str(uuid4())}),
        ("patch", {"created_at": "2026-01-01T00:00:00Z"}),
        ("patch", {"unknown_field": "unexpected"}),
    ],
)
def test_update_rejects_unknown_or_readonly_fields(
    client: TestClient,
    method: str,
    payload: dict,
) -> None:
    created = client.post(
        "/movies",
        json={"title": "Original Movie"},
    ).json()

    response = client.request(
        method.upper(),
        f"/movies/{created['id']}",
        json=payload,
    )

    assert response.status_code == 422

    retrieved = client.get(f"/movies/{created['id']}")

    assert retrieved.status_code == 200
    assert retrieved.json()["title"] == "Original Movie"
