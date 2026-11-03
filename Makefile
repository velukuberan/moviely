.DEFAULT_GOAL := help

COMPOSE := docker compose -f compose.yaml -f deploy/local/compose.yaml

MIGRATION_COMPOSE := docker compose \
	-f compose.yaml \
	-f deploy/local/compose.yaml \
	-f deploy/local/compose.migrations.yaml

.PHONY: help up build rebuild down restart logs status clean destroy \
        test-db test lint format format-check lock-check check compose-check \
        db-current db-upgrade db-history db-check db-test-setup db-revision

help:
	@echo "Moviely — Development Commands"
	@echo ""
	@echo "Docker:"
	@echo "  make up             Start services"
	@echo "  make build          Build images without starting"
	@echo "  make rebuild        Rebuild and recreate services"
	@echo "  make down           Stop and remove containers"
	@echo "  make restart        Restart running services"
	@echo "  make logs           Follow service logs"
	@echo "  make status         Show container status"
	@echo "  make clean          Stop and remove containers"
	@echo "  make destroy        Remove containers and volumes"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run pytest"
	@echo "  make lint           Check Ruff linting"
	@echo "  make format         Format Python code"
	@echo "  make format-check   Check formatting"
	@echo "  make lock-check     Verify uv.lock"
	@echo "  make check          Run all quality checks"
	@echo "  make compose-check  Validate Docker Compose configuration"
	@echo ""
	@echo "Database:"
	@echo "  make db-check       Verify PostgreSQL connectivity"
	@echo "  make db-current     Show and verify current migration"
	@echo "  make db-upgrade     Apply pending migrations"
	@echo "  make db-history     Show migration history"
	@echo "  make test-db        Run PostgreSQL integration tests"
	@echo "  make db-test-setup  Verify and provision the test database"
	@echo "  make db-revision MSG='description'  Generate Alembic migration"

up:
	$(COMPOSE) up -d

build:
	$(COMPOSE) build

rebuild:
	$(COMPOSE) up -d --build --force-recreate

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

logs:
	$(COMPOSE) logs -f

status:
	$(COMPOSE) ps

clean: down

destroy:
	@printf "This will permanently delete Moviely's Docker volumes.\n"
	@printf "Type 'destroy' to confirm: "
	@read answer; \
	if [ "$$answer" = "destroy" ]; then \
		$(COMPOSE) down -v --remove-orphans; \
	else \
		echo "Cancelled."; \
	fi


test-db: db-test-setup
	$(COMPOSE) run --rm test \
		pytest tests/integration/db -v

test:
	uv run pytest -v

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

lock-check:
	uv lock --check

check: test lint format-check lock-check

compose-check:
	$(COMPOSE) --profile test config --quiet

db-current:
	$(COMPOSE) exec -T api alembic current --check-heads

db-upgrade:
	$(COMPOSE) exec -T api alembic upgrade head

db-history:
	$(COMPOSE) exec -T api alembic history --verbose

db-check:
	$(COMPOSE) exec -T api python -c 'from sqlalchemy import text; from moviely.db.session import get_engine; connection = get_engine().connect(); assert connection.execute(text("SELECT 1")).scalar_one() == 1; connection.close(); print("Database connection OK")'

db-test-setup:
	./scripts/provision-test-db.sh

db-revision:
	@test -n "$(MSG)" || (echo "Usage: make db-revision MSG='migration description'"; exit 1)
	$(MIGRATION_COMPOSE) run --rm test \
		alembic revision --autogenerate -m "$(MSG)"
