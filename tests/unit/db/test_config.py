from moviely.config import get_database_url


def test_database_url_supports_special_characters(monkeypatch):
    monkeypatch.setenv("POSTGRES_USER", "moviely")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test@pass:/word")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "moviely_test")

    url = get_database_url()

    assert url.drivername == "postgresql+psycopg"
    assert url.username == "moviely"
    assert url.password == "test@pass:/word"
    assert url.host == "localhost"
    assert url.port == 5432
    assert url.database == "moviely_test"
