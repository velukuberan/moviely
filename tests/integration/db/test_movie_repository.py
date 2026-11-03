import os
from collections.abc import Iterator
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from moviely.db.session import get_engine
from moviely.movies.models import Movie
from moviely.movies.repository import MovieRepository

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
            with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
                yield db
        finally:
            transaction.rollback()


def test_add_and_get_movie(session: Session) -> None:
    repository = MovieRepository(session)

    movie = repository.add(Movie(title="Repository Test"))

    assert movie.id is not None

    retrieved = repository.get(movie.id)

    assert retrieved is not None
    assert retrieved.title == "Repository Test"


def test_get_missing_movie(session: Session) -> None:
    repository = MovieRepository(session)

    assert repository.get(uuid4()) is None


def test_list_movies_with_pagination(session: Session) -> None:
    repository = MovieRepository(session)

    movies = [repository.add(Movie(title=f"Pagination Movie {index}")) for index in range(5)]

    expected = sorted(
        movies,
        key=lambda movie: (movie.created_at, movie.id),
        reverse=True,
    )

    first_page = repository.list(offset=0, limit=2)
    second_page = repository.list(offset=2, limit=2)
    third_page = repository.list(offset=4, limit=2)

    assert [movie.id for movie in first_page] == [movie.id for movie in expected[:2]]
    assert [movie.id for movie in second_page] == [movie.id for movie in expected[2:4]]
    assert [movie.id for movie in third_page] == [movie.id for movie in expected[4:]]


def test_update_movie(session: Session) -> None:
    repository = MovieRepository(session)

    movie = repository.add(Movie(title="Original Title"))

    movie.title = "Updated Title"
    repository.flush()
    session.refresh(movie)

    assert movie.title == "Updated Title"


def test_delete_movie(session: Session) -> None:
    repository = MovieRepository(session)

    movie = repository.add(Movie(title="Delete Me"))
    movie_id = movie.id

    repository.delete(movie)

    assert repository.get(movie_id) is None


def test_repository_does_not_commit(session: Session) -> None:
    repository = MovieRepository(session)

    movie = repository.add(Movie(title="Uncommitted Movie"))

    assert session.scalar(select(Movie.id).where(Movie.id == movie.id)) == movie.id

    assert session.in_transaction()
