FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /uvx /bin/

WORKDIR /app

ENV UV_PYTHON_DOWNLOADS=0 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
COPY alembic.ini ./
COPY migrations/ ./migrations/

FROM base AS application

RUN uv sync --locked --no-dev --no-editable

EXPOSE 8000

CMD ["uvicorn", "moviely.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS test

RUN uv sync --locked --no-editable

COPY tests/ ./tests/

CMD ["pytest", "-v"]
