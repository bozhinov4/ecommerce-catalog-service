.PHONY: down format init install lint migrate run seed test up

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
