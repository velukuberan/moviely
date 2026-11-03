from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from moviely.db.base import Base
from moviely.movies.enums import MovieStatus


class Movie(Base):
    __tablename__ = "movies"

    __table_args__ = (
        CheckConstraint(
            "title ~ '[^[:space:]]'",
            name="title_nonblank",
        ),
        CheckConstraint(
            "runtime_minutes IS NULL OR runtime_minutes > 0",
            name="runtime_positive",
        ),
        CheckConstraint(
            "status IN ('announced', 'released', 'cancelled')",
            name="status_valid",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    overview: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    release_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    runtime_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    original_language: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MovieStatus.ANNOUNCED.value,
        server_default=text("'announced'"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
