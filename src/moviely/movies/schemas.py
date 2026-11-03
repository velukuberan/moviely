from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from moviely.movies.enums import MovieStatus


class StrictMovieInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MovieFields(StrictMovieInput):
    title: str = Field(min_length=1, max_length=255)
    overview: str | None = None
    release_date: date | None = None
    runtime_minutes: int | None = Field(default=None, gt=0)
    original_language: str | None = Field(default=None, max_length=10)
    status: MovieStatus = MovieStatus.ANNOUNCED

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Title must not be blank")
        return value


class MovieCreate(MovieFields):
    pass


class MovieReplace(MovieFields):
    pass


class MoviePatch(StrictMovieInput):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    overview: str | None = None
    release_date: date | None = None
    runtime_minutes: int | None = Field(default=None, gt=0)
    original_language: str | None = Field(default=None, max_length=10)
    status: MovieStatus | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Title must not be blank")
        return value

    @field_validator("title", "status")
    @classmethod
    def reject_null_required_fields(cls, value: object) -> object:
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class MovieResponse(MovieFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
