from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from moviely.movies.enums import MovieStatus
from moviely.movies.models import Movie
from moviely.movies.schemas import MovieCreate, MoviePatch, MovieReplace, MovieResponse


def test_create_movie_with_title_only() -> None:
    movie = MovieCreate(title="Interstellar")

    assert movie.title == "Interstellar"
    assert movie.status == MovieStatus.ANNOUNCED
    assert movie.overview is None
    assert movie.runtime_minutes is None


def test_create_movie_with_all_fields() -> None:
    movie = MovieCreate(
        title="Interstellar",
        overview="Science fiction",
        release_date=date(2014, 11, 7),
        runtime_minutes=169,
        original_language="en",
        status=MovieStatus.RELEASED,
    )

    assert movie.release_date == date(2014, 11, 7)
    assert movie.runtime_minutes == 169
    assert movie.status == MovieStatus.RELEASED


@pytest.mark.parametrize("title", ["", "   ", "\t", "\n"])
def test_create_rejects_blank_title(title: str) -> None:
    with pytest.raises(ValidationError):
        MovieCreate(title=title)


@pytest.mark.parametrize("runtime", [0, -1, -120])
def test_create_rejects_invalid_runtime(runtime: int) -> None:
    with pytest.raises(ValidationError):
        MovieCreate(title="Test Movie", runtime_minutes=runtime)


def test_replace_requires_title() -> None:
    with pytest.raises(ValidationError):
        MovieReplace()


def test_replace_resets_optional_fields() -> None:
    movie = MovieReplace(title="Replacement Movie")

    assert movie.overview is None
    assert movie.runtime_minutes is None
    assert movie.status == MovieStatus.ANNOUNCED


def test_patch_allows_empty_payload() -> None:
    movie = MoviePatch()

    assert movie.model_dump(exclude_unset=True) == {}


def test_patch_preserves_omitted_fields() -> None:
    movie = MoviePatch(title="Updated Title")

    assert movie.model_dump(exclude_unset=True) == {"title": "Updated Title"}


def test_patch_allows_null_for_optional_field() -> None:
    movie = MoviePatch(overview=None)

    assert movie.model_dump(exclude_unset=True) == {"overview": None}


@pytest.mark.parametrize("field", ["title", "status"])
def test_patch_rejects_null_required_fields(field: str) -> None:
    with pytest.raises(ValidationError):
        MoviePatch.model_validate({field: None})


def test_patch_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        MoviePatch(status="unknown")


def test_movie_response_from_orm() -> None:
    movie_id = uuid4()
    timestamp = datetime.now(UTC)

    movie = Movie(
        id=movie_id,
        title="Interstellar",
        runtime_minutes=169,
        status=MovieStatus.RELEASED.value,
        created_at=timestamp,
        updated_at=timestamp,
    )

    response = MovieResponse.model_validate(movie)

    assert response.id == movie_id
    assert response.title == "Interstellar"
    assert response.runtime_minutes == 169
    assert response.status == MovieStatus.RELEASED
    assert response.created_at == timestamp
    assert response.updated_at == timestamp
