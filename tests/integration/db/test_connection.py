import os

import pytest
from sqlalchemy import text

from moviely.config import get_database_url
from moviely.db.session import get_engine

pytestmark = pytest.mark.skipif(
    os.getenv("MOVIELY_TEST_POSTGRES") != "1",
    reason="Requires PostgreSQL integration environment",
)


def test_postgresql_connection() -> None:
    url = get_database_url()

    assert url.username == "moviely_test"
    assert url.database == "moviely_test"

    with get_engine().connect() as connection:
        result = connection.execute(text("SELECT current_database(), current_user")).one()

    assert result == ("moviely_test", "moviely_test")
