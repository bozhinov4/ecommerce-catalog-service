.DEFAULT_GOAL := help

.PHONY: down format help init install lint migrate run seed test up

help:
	@printf '%s\n' \
		'Available targets:' \
		'  make init     Install dependencies, migrate, and seed demo data' \
		'  make install  Install dependencies from the lockfile' \
		'  make migrate  Apply database migrations' \
		'  make seed     Create or refresh the demo catalog' \
		'  make run      Start the local development server' \
		'  make format   Format and automatically fix lint issues' \
		'  make lint     Check formatting, linting, and types' \
		'  make test     Run tests with coverage' \
		'  make up       Build and start the Docker Compose stack' \
		'  make down     Stop the Docker Compose stack'

init: install migrate seed

install:
	uv sync --locked

format:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff format --check .
	uv run ruff check .
	uv run pyright

test:
	uv run pytest --cov --cov-report=term-missing

migrate:
	uv run alembic upgrade head

seed:
	uv run catalog-seed

run:
	uv run catalog-api

up:
	docker compose up --build

down:
	docker compose down
