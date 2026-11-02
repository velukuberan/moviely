import os

from sqlalchemy import URL


def get_database_url() -> URL:
    return URL.create(
        drivername="postgresql+psycopg",
        username=os.environ.get("POSTGRES_USER", "moviely"),
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ.get("POSTGRES_HOST", "db"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "moviely"),
    )
