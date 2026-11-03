from uuid import UUID

from sqlalchemy.orm import Session

from moviely.movies.models import Movie
from moviely.movies.repository import MovieRepository
from moviely.movies.schemas import MovieCreate, MoviePatch, MovieReplace


class MovieService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = MovieRepository(session)

    def create(self, payload: MovieCreate) -> Movie:
        movie = Movie(**payload.model_dump(mode="python"))

        try:
            self.repository.add(movie)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        self.session.refresh(movie)
        return movie

    def get(self, movie_id: UUID) -> Movie | None:
        return self.repository.get(movie_id)

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Movie]:
        return self.repository.list(offset=offset, limit=limit)

    def replace(self, movie_id: UUID, payload: MovieReplace) -> Movie | None:
        movie = self.repository.get(movie_id)

        if movie is None:
            return None

        values = payload.model_dump(mode="python")

        for field, value in values.items():
            setattr(movie, field, value)

        return self._save(movie)

    def patch(self, movie_id: UUID, payload: MoviePatch) -> Movie | None:
        movie = self.repository.get(movie_id)

        if movie is None:
            return None

        changes = payload.model_dump(
            mode="python",
            exclude_unset=True,
        )

        if not changes:
            return movie

        for field, value in changes.items():
            setattr(movie, field, value)

        return self._save(movie)

    def delete(self, movie_id: UUID) -> bool:
        movie = self.repository.get(movie_id)

        if movie is None:
            return False

        try:
            self.repository.delete(movie)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        return True

    def _save(self, movie: Movie) -> Movie:
        try:
            self.repository.flush()
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        self.session.refresh(movie)
        return movie
