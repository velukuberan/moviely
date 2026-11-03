from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from moviely.movies.models import Movie


class MovieRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, movie_id: UUID) -> Movie | None:
        return self.session.get(Movie, movie_id)

    def list(self, *, offset: int = 0, limit: int = 20) -> list[Movie]:
        statement = (
            select(Movie)
            .order_by(Movie.created_at.desc(), Movie.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def add(self, movie: Movie) -> Movie:
        self.session.add(movie)
        self.session.flush()
        return movie

    def delete(self, movie: Movie) -> None:
        self.session.delete(movie)
        self.session.flush()

    def flush(self) -> None:
        self.session.flush()
