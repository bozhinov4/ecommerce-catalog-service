.PHONY: format install lint migrate run test up down

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

run:
	uv run catalog-api

up:
	docker compose up --build

down:
	docker compose down
