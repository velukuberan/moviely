from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from moviely.db import session as db_session


def test_session_executes_query(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")

    try:
        monkeypatch.setattr(
            db_session,
            "get_engine",
            lambda: engine,
        )
        db_session.get_session_factory.cache_clear()

        session_generator = db_session.get_session()

        try:
            session = next(session_generator)

            assert isinstance(session, Session)
            assert session.execute(text("SELECT 1")).scalar_one() == 1
        finally:
            session_generator.close()

        assert not session.in_transaction()
    finally:
        db_session.get_session_factory.cache_clear()
        engine.dispose()
