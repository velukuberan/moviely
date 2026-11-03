import os
from collections.abc import Iterator
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from moviely.db.session import get_engine
from moviely.movies.enums import MovieStatus
from moviely.movies.schemas import MovieCreate, MoviePatch, MovieReplace
from moviely.movies.service import MovieService

pytestmark = pytest.mark.skipif(
    os.getenv("MOVIELY_TEST_POSTGRES") != "1",
    reason="Requires PostgreSQL integration environment",
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = get_engine()

    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as db:
                yield db
        finally:
            transaction.rollback()


def test_create_movie(session: Session) -> None:
    service = MovieService(session)

    movie = service.create(
        MovieCreate(
            title="Interstellar",
            runtime_minutes=169,
            status=MovieStatus.RELEASED,
        )
    )

    assert movie.id is not None
    assert movie.title == "Interstellar"
    assert movie.runtime_minutes == 169
    assert movie.status == MovieStatus.RELEASED
    assert movie.created_at is not None
    assert movie.updated_at is not None


def test_get_and_list_movies(session: Session) -> None:
    service = MovieService(session)

    movie = service.create(MovieCreate(title="Service Test"))

    retrieved = service.get(movie.id)

    assert retrieved is not None
    assert retrieved.id == movie.id

    movies = service.list()

    assert any(item.id == movie.id for item in movies)
    assert service.get(uuid4()) is None


def test_create_rolls_back_on_database_error(session: Session) -> None:
    service = MovieService(session)

    # Bypass Pydantic validation intentionally to test the
    # service's behavior when PostgreSQL rejects an INSERT.
    invalid_payload = MovieCreate.model_construct(title="   ")

    with pytest.raises(IntegrityError):
        service.create(invalid_payload)

    assert not session.in_transaction()

    # The session must remain usable after the rollback.
    movie = service.create(MovieCreate(title="Recovery Test"))

    assert movie.id is not None
    assert movie.title == "Recovery Test"


def test_replace_movie_resets_optional_fields(session: Session) -> None:
    service = MovieService(session)

    movie = service.create(
        MovieCreate(
            title="Original Movie",
            overview="Original overview",
            runtime_minutes=120,
            original_language="en",
            status=MovieStatus.RELEASED,
        )
    )

    replaced = service.replace(
        movie.id,
        MovieReplace(title="Replacement Movie"),
    )

    assert replaced is not None
    assert replaced.id == movie.id
    assert replaced.title == "Replacement Movie"
    assert replaced.overview is None
    assert replaced.runtime_minutes is None
    assert replaced.original_language is None
    assert replaced.status == MovieStatus.ANNOUNCED


def test_patch_movie_preserves_omitted_fields(session: Session) -> None:
    service = MovieService(session)

    movie = service.create(
        MovieCreate(
            title="Original Movie",
            overview="Original overview",
            runtime_minutes=120,
            status=MovieStatus.RELEASED,
        )
    )

    patched = service.patch(
        movie.id,
        MoviePatch(title="Updated Movie"),
    )

    assert patched is not None
    assert patched.title == "Updated Movie"
    assert patched.overview == "Original overview"
    assert patched.runtime_minutes == 120
    assert patched.status == MovieStatus.RELEASED


def test_patch_movie_can_clear_nullable_field(session: Session) -> None:
    service = MovieService(session)

    movie = service.create(
        MovieCreate(
            title="Original Movie",
            overview="To be cleared",
        )
    )

    patched = service.patch(
        movie.id,
        MoviePatch(overview=None),
    )

    assert patched is not None
    assert patched.overview is None


def test_empty_patch_does_not_modify_movie(session: Session) -> None:
    service = MovieService(session)
    movie = service.create(MovieCreate(title="Original Movie"))

    original_updated_at = movie.updated_at

    patched = service.patch(movie.id, MoviePatch())

    assert patched is not None
    assert patched.title == "Original Movie"
    assert patched.updated_at == original_updated_at


def test_delete_movie(session: Session) -> None:
    service = MovieService(session)
    movie = service.create(MovieCreate(title="Delete Me"))
    movie_id = movie.id

    assert service.delete(movie_id) is True
    assert service.get(movie_id) is None


def test_missing_movie_operations(session: Session) -> None:
    service = MovieService(session)
    missing_id = uuid4()

    assert (
        service.replace(
            missing_id,
            MovieReplace(title="Replacement"),
        )
        is None
    )

    assert (
        service.patch(
            missing_id,
            MoviePatch(title="Updated"),
        )
        is None
    )

    assert service.delete(missing_id) is False
