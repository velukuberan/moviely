# Moviely

An open-source Movie REST API built with Python and FastAPI.

Moviely is a standalone REST API project designed to provide movie-related resources and HTTP testing capabilities. It can be deployed locally or on remote servers and used to test HTTP clients such as [Restling](https://github.com/velukuberan).

## Technology Stack

- **Python 3.13** — Programming language
- **FastAPI** — REST API framework
- **Uvicorn** — ASGI server
- **uv** — Python dependency and environment management
- **PostgreSQL 17** — Database service (application integration planned)
- **Mailpit** — Local email testing (application integration planned)
- **Docker Compose** — Local infrastructure
- **pytest** — Automated testing
- **Ruff** — Linting and formatting

Remote deployment configuration will be introduced in a subsequent milestone.

## Requirements

For host-based Python development:

- [uv](https://docs.astral.sh/uv/)

For containerized local development:

- Docker Engine
- Docker Compose v2
- GNU Make

Python 3.13 can be installed and managed through `uv`.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/velukuberan/moviely.git
cd moviely
```

### 2. Install Python

```bash
uv python install 3.13
```

### 3. Install project dependencies

```bash
uv sync
```

This creates a managed `.venv` environment and installs Moviely along with its development dependencies.

The dependency versions are recorded in `uv.lock` to support reproducible installations.

## Running the Application Directly

Start the FastAPI development server:

```bash
uv run uvicorn moviely.main:app --reload
```

The `--reload` option automatically restarts the application when source files change. It should only be used during development.

Once running, the following endpoints are available:

| Endpoint | URL |
|---|---|
| API root | http://127.0.0.1:8000 |
| Health check | http://127.0.0.1:8000/health |
| Swagger UI | http://127.0.0.1:8000/docs |
| OpenAPI schema | http://127.0.0.1:8000/openapi.json |

The API root may return `404 Not Found` until a root endpoint is introduced.

## Docker — Local Development

Moviely provides a containerized local environment containing FastAPI, PostgreSQL, and Mailpit.

### Configure the environment

From the repository root:

```bash
cp .env.example .env
chmod 600 .env
```

Edit `.env` and replace `POSTGRES_PASSWORD=change-me-local` with a local development password before starting the services. Keep `.env` private; it must not be committed to Git. For this initial Compose configuration, use a URL-safe password because it is interpolated into `DATABASE_URL`.

### Start the services

```bash
make up
```

On first startup, Docker Compose builds the application image if it does not already exist. PostgreSQL data is stored in a persistent Docker volume.

### Available services

| Service | Address |
|---|---|
| FastAPI | http://127.0.0.1:8000 |
| Swagger UI | http://127.0.0.1:8000/docs |
| Health endpoint | http://127.0.0.1:8000/health |
| Mailpit web inbox | http://127.0.0.1:8025 |
| PostgreSQL | Internal Docker network only (`db:5432`) |
| Mailpit SMTP | Internal Docker network only (`mailpit:1025`) |

The API and Mailpit web UI are bound to the host's loopback interface for local testing. PostgreSQL and SMTP ports are not published to the host.

### Managing Docker services

All Makefile Docker commands target the **local** Compose configuration (`compose.yaml` plus `deploy/local/compose.yaml`).

| Command | Description |
|---|---|
| `make help` | List available commands |
| `make up` | Start services; build missing images if necessary |
| `make build` | Build images without starting services |
| `make rebuild` | Rebuild and recreate services |
| `make down` | Stop and remove containers while preserving volumes |
| `make restart` | Restart existing containers |
| `make logs` | Follow container logs (`Ctrl+C` to stop following) |
| `make status` | Display service status |
| `make clean` | Same as `make down`; retains volumes |
| `make destroy` | Remove containers and persistent volumes (requires confirmation) |
| `make check` | Run tests, linting, formatting checks, and lockfile verification |

Check running services:

```bash
make status
```

Follow logs:

```bash
make logs
```

Rebuild the image after changing application source code:

```bash
make rebuild
```

Stop the environment without deleting PostgreSQL data:

```bash
make down
```

To remove the local containers **and their persistent database data**:

```bash
make destroy
```

**Warning:** `make destroy` permanently deletes the project's Docker volumes.

### Validate the Compose configuration

```bash
docker compose \
  -f compose.yaml \
  -f deploy/local/compose.yaml \
  config --quiet
```

### Development notes

- The existing `uv run` workflow remains available for running FastAPI directly on the host.
- The Docker image installs production dependencies using the committed `uv.lock`.
- Source changes require rebuilding the API image in this initial configuration.
- PostgreSQL and SMTP configuration are provisioned, but application-level database and email integration will be implemented in subsequent milestones.
- This local Compose configuration is not intended for public deployment.

## Health Check

Request:

```http
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "moviely"
}
```

## Development Commands

All development commands are executed from the repository root.

### Testing

Run all tests with verbose output:

```bash
uv run pytest -v
```

Run a specific test file:

```bash
uv run pytest tests/integration/api/test_health.py -v
```

Run a specific test:

```bash
uv run pytest \
  tests/integration/api/test_health.py::test_health_returns_success -v
```

### Linting

Check the codebase for linting violations:

```bash
uv run ruff check .
```

Automatically fix supported issues:

```bash
uv run ruff check . --fix
```

### Formatting

Check whether the code follows Ruff's formatting rules without modifying files:

```bash
uv run ruff format --check .
```

Automatically format the code:

```bash
uv run ruff format .
```

### Dependency Management

Add a runtime dependency:

```bash
uv add <package-name>
```

Add a development dependency:

```bash
uv add --dev <package-name>
```

Remove a dependency:

```bash
uv remove <package-name>
```

Remove a development dependency:

```bash
uv remove --dev <package-name>
```

Synchronize dependencies:

```bash
uv sync
```

Verify that the lockfile is current:

```bash
uv lock --check
```

Both `pyproject.toml` and `uv.lock` must be committed to Git.

## Before Committing

Run all four checks before committing changes or opening a pull request:

```bash
# 1. Run tests
uv run pytest -v

# 2. Check linting
uv run ruff check .

# 3. Check formatting
uv run ruff format --check .

# 4. Verify dependency lockfile
uv lock --check
```

Or use the Makefile shortcut:

```bash
make check
```

All checks should pass.

If formatting issues are found, run:

```bash
uv run ruff format .
```

If automatically fixable linting issues are found, run:

```bash
uv run ruff check . --fix
```

Review all changes and rerun the checks before committing.

## Git Workflow

Moviely uses the `MOV` prefix for feature branches, commits and pull requests.

Example branch:

```bash
git switch -c MOV-001
```

Example commit:

```bash
git commit -m "MOV-001: Initialize FastAPI project foundation"
```

Example pull request title:

```text
MOV-001: Initialize FastAPI Project Foundation
```

Each pull request should contain focused changes, appropriate tests and updated documentation when relevant.

## License

Moviely is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.
