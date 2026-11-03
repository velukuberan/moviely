from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from moviely.db.session import get_session
from moviely.movies.schemas import (
    MovieCreate,
    MoviePatch,
    MovieReplace,
    MovieResponse,
)
from moviely.movies.service import MovieService

router = APIRouter(prefix="/movies", tags=["Movies"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.post(
    "",
    response_model=MovieResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_movie(
    payload: MovieCreate,
    session: SessionDep,
) -> MovieResponse:
    movie = MovieService(session).create(payload)
    return MovieResponse.model_validate(movie)


@router.get(
    "",
    response_model=list[MovieResponse],
)
def list_movies(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[MovieResponse]:
    movies = MovieService(session).list(
        offset=offset,
        limit=limit,
    )

    return [MovieResponse.model_validate(movie) for movie in movies]


@router.get(
    "/{movie_id}",
    response_model=MovieResponse,
)
def get_movie(
    movie_id: UUID,
    session: SessionDep,
) -> MovieResponse:
    movie = MovieService(session).get(movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    return MovieResponse.model_validate(movie)


@router.put(
    "/{movie_id}",
    response_model=MovieResponse,
)
def replace_movie(
    movie_id: UUID,
    payload: MovieReplace,
    session: SessionDep,
) -> MovieResponse:
    movie = MovieService(session).replace(movie_id, payload)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    return MovieResponse.model_validate(movie)


@router.patch(
    "/{movie_id}",
    response_model=MovieResponse,
)
def patch_movie(
    movie_id: UUID,
    payload: MoviePatch,
    session: SessionDep,
) -> MovieResponse:
    movie = MovieService(session).patch(movie_id, payload)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    return MovieResponse.model_validate(movie)


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_movie(
    movie_id: UUID,
    session: SessionDep,
) -> Response:
    deleted = MovieService(session).delete(movie_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.head("/{movie_id}")
def head_movie(
    movie_id: UUID,
    session: SessionDep,
) -> Response:
    movie = MovieService(session).get(movie_id)

    if movie is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return Response(status_code=status.HTTP_200_OK)
