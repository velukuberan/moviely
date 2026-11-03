import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import insert, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from moviely.db.session import get_engine
from moviely.movies.enums import MovieStatus
from moviely.movies.models import Movie

pytestmark = pytest.mark.skipif(
    os.getenv("MOVIELY_TEST_POSTGRES") != "1",
    reason="Requires PostgreSQL integration environment",
)


def test_create_and_retrieve_movie() -> None:
    engine = get_engine()

    # Keep test changes inside a transaction.
    # Rolling it back prevents test data from persisting.
    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            with Session(bind=connection) as session:
                movie = Movie(
                    title="Example Movie",
                    overview="A movie used for integration testing.",
                    runtime_minutes=120,
                    original_language="en",
                    status=MovieStatus.RELEASED.value,
                )

                session.add(movie)
                session.flush()

                assert isinstance(movie.id, UUID)
                assert movie.created_at is not None
                assert movie.updated_at is not None

                result = session.scalar(select(Movie).where(Movie.id == movie.id))

                assert result is not None
                assert result.title == "Example Movie"
                assert result.runtime_minutes == 120
                assert result.status == MovieStatus.RELEASED.value

        finally:
            transaction.rollback()


@pytest.mark.parametrize(
    "invalid_title",
    ["", "   ", "\t", "\n", " \t\n "],
)
def test_rejects_blank_title(invalid_title: str) -> None:
    engine = get_engine()

    with engine.begin() as connection, pytest.raises(IntegrityError):
        connection.execute(insert(Movie).values(title=invalid_title))


@pytest.mark.parametrize(
    "invalid_runtime",
    [0, -1, -120],
)
def test_rejects_invalid_runtime(invalid_runtime: int) -> None:
    engine = get_engine()

    with engine.begin() as connection, pytest.raises(IntegrityError):
        connection.execute(
            insert(Movie).values(
                title="Invalid Runtime",
                runtime_minutes=invalid_runtime,
            )
        )


def test_rejects_invalid_status() -> None:
    engine = get_engine()

    with engine.begin() as connection, pytest.raises(IntegrityError):
        connection.execute(
            insert(Movie).values(
                title="Invalid Status",
                status="unknown",
            )
        )


def test_defaults_to_announced_status() -> None:
    engine = get_engine()

    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            result = connection.execute(
                insert(Movie).values(title="Default Status Movie").returning(Movie.status)
            )

            assert result.scalar_one() == MovieStatus.ANNOUNCED.value

        finally:
            transaction.rollback()


@pytest.mark.parametrize(
    "field",
    ["id", "title", "status", "created_at", "updated_at"],
)
def test_rejects_null_required_fields(field: str) -> None:
    engine = get_engine()

    values = {
        "id": str(uuid4()),
        "title": "Required Fields Test",
        "status": "announced",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    values[field] = None

    with engine.begin() as connection, pytest.raises(IntegrityError):
        connection.execute(
            text(
                """
                INSERT INTO movies
                    (id, title, status, created_at, updated_at)
                VALUES
                    (:id, :title, :status, :created_at, :updated_at)
                """
            ),
            values,
        )


def test_database_generates_timestamps() -> None:
    engine = get_engine()

    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            result = connection.execute(
                insert(Movie)
                .values(title="Timestamp Test")
                .returning(Movie.created_at, Movie.updated_at)
            ).one()

            assert result.created_at is not None
            assert result.updated_at is not None
            assert result.created_at.tzinfo is not None
            assert result.updated_at.tzinfo is not None

        finally:
            transaction.rollback()


def test_updating_movie_changes_updated_at() -> None:
    engine = get_engine()

    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            with Session(bind=connection) as session:
                movie = Movie(title="Before Update")
                session.add(movie)
                session.flush()

                original_updated_at = movie.updated_at

                # Make the update timestamp deterministic by setting
                # the original timestamp to a past value.
                movie.updated_at = datetime(2020, 1, 1, tzinfo=UTC)
                session.flush()

                movie.title = "After Update"
                session.flush()
                session.refresh(movie)

                assert movie.title == "After Update"
                assert movie.updated_at > datetime(2020, 1, 1, tzinfo=UTC)
                assert movie.updated_at >= original_updated_at

        finally:
            transaction.rollback()
