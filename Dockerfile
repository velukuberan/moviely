FROM python:3.13-slim

# Pin uv to a known release.
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /uvx /bin/

WORKDIR /app

ENV UV_PYTHON_DOWNLOADS=0 \
    UV_NO_DEV=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install from the committed lockfile, excluding development tools.
RUN uv sync --locked --no-dev --no-editable

EXPOSE 8000

CMD ["uvicorn", "moviely.main:app", "--host", "0.0.0.0", "--port", "8000"]

