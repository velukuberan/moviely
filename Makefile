
.DEFAULT_GOAL := help

COMPOSE := docker compose -f compose.yaml -f deploy/local/compose.yaml

.PHONY: help up build rebuild down restart logs status clean destroy \
        test lint format format-check lock-check check

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

