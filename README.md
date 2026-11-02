# Moviely

An open-source Movie REST API built with Python and FastAPI.

Moviely is a standalone REST API project designed to provide movie-related resources and HTTP testing capabilities. It can be deployed locally or on remote servers and used to test HTTP clients such as [Restling](https://github.com/velukuberan).

## Technology Stack

- **Python 3.13** — Programming language
- **FastAPI** — REST API framework
- **Uvicorn** — ASGI server
- **uv** — Python dependency and environment management
- **pytest** — Automated testing
- **Ruff** — Linting and formatting

PostgreSQL, Docker, Mailpit and deployment configurations will be introduced in subsequent milestones.

## Requirements

- [uv](https://docs.astral.sh/uv/)

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

## Running the Application

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

### Managing Docker Services

Moviely provides a Makefile for managing the local development environment.

| Command | Description |
|---|---|
| `make up` | Build and start FastAPI, PostgreSQL, and Mailpit |
| `make down` | Stop and remove containers, preserving volumes |
| `make restart` | Restart existing services |
| `make rebuild` | Rebuild and recreate services |
| `make logs` | Follow container logs |
| `make status` | Display service status |
| `make clean` | Remove containers while retaining data |
| `make destroy` | Remove containers and persistent volumes (requires confirmation) |
| `make check` | Run tests, linting, formatting checks, and lockfile verification |

Start the environment:

```bash
make up
```

Check running services:

```bash
make status
```

View logs:

```bash
make logs
```

Stop the environment without deleting PostgreSQL data:

```bash
make down
```

To completely remove the local environment, including persistent database data:

```bash
make destroy
```

**Warning:** `make destroy` permanently removes the project's Docker volumes.

For all available commands, run:

```bash
make help
```

### Development Notes

- The existing `uv run` workflow remains available for running FastAPI directly on the host.
- The Docker image installs dependencies using the committed `uv.lock` file.
- Source changes require rebuilding the API image in this initial configuration.
- PostgreSQL and SMTP configuration are provisioned, but their application integrations will be implemented in subsequent milestones.

### Health Check

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
