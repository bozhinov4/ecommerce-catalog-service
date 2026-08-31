# Development Guidelines

## Scope

- This repository is a FastAPI and PostgreSQL service managed with `uv`.
- Use the `gh` CLI for GitHub platform operations.

## GitHub Safety

- Confirm `gh` is authenticated as `bozhinov4` before GitHub writes.
- Target `bozhinov4/ecommerce-catalog-service` explicitly in `gh` commands.
- After every GitHub write, read back the resulting URL, state, or workflow status.
- Do not force-push, merge or close pull requests, delete artifacts, or change
  repository visibility unless the user explicitly requests it.
- Use local `git` for source control and `gh` for GitHub-hosted operations.

## Workflow

- Add dependencies with `uv add`; never edit lockfile contents manually.
- Run commands through `uv run`.
- Keep commits small with short, outcome-focused subjects.
- Add tests for every behavior change.
- Preserve backward compatibility unless a breaking API change is explicitly
  requested and documented.

## Architecture

- Keep API routers focused on HTTP parsing, status codes, and response contracts.
- Keep business rules and queries in services so they remain independently testable.
- Use SQLAlchemy models only for persistence and Pydantic schemas for external
  request and response contracts.
- Load runtime configuration from the environment through the settings layer.
- Prefer small changes that preserve the existing module boundaries.

## API Conventions

- Keep public endpoints versioned under `/api/v1`.
- Use consistent HTTP status codes and error response structures.
- Bound and validate pagination on every collection endpoint.
- Treat the generated OpenAPI schema as a public contract.
- Do not introduce a breaking API change without explicit approval and documentation.

## Data and Migrations

- Use `Decimal` and PostgreSQL `NUMERIC` for monetary values; never use binary
  floating-point types for prices.
- Store timestamps as timezone-aware values and use UTC at system boundaries.
- Add indexes for demonstrated query patterns, not speculatively.
- Create an Alembic migration for every schema change and verify both upgrade and
  downgrade paths against PostgreSQL.
- Keep schema migrations separate from demo data.
- Keep demo seeds idempotent and opt-in outside the local Docker Compose setup.
- Do not perform a destructive migration without an explicit rollback plan.

## Dependencies

- Justify every new production dependency and prefer the standard library or an
  existing dependency when either is sufficient.
- Keep the Python version, `.python-version`, and Docker runtime aligned.
- Review major dependency upgrades manually, even when their automated checks pass.
- Commit `pyproject.toml` and `uv.lock` together whenever dependency resolution
  changes.

## Quality Gates

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --cov --cov-report=term-missing
```

- Maintain 100% statement and branch coverage for the application package.
- Do not add coverage exclusions merely to satisfy the threshold; document any
  genuinely unreachable platform-specific code before excluding it.
- Validate the Docker build when runtime code, dependencies, migrations, or startup
  behavior changes.

## Security and Delivery

- Never commit credentials, tokens, `.env` files, or production data.
- Keep configuration environment-driven and update `.env.example` for new settings.
- Preserve the non-root runtime container and pinned GitHub Action revisions.
- Ensure a fresh clone remains runnable with `docker compose up --build`.

## Observability

- Never log credentials, secrets, or complete sensitive request payloads.
- Use structured, contextual logs for new operational events and failures.
- Keep `/health` lightweight and independent of downstream services so it remains
  a process liveness check.
- Add a separate readiness check if deployment orchestration needs database or other
  dependency health.

## Definition of Done

A change is complete only when all applicable items are satisfied:

- Formatting, linting, strict type checks, tests, and coverage gates pass.
- Statement and branch coverage remain at 100%.
- Relevant documentation, OpenAPI behavior, and `.env.example` are current.
- Schema changes include a reversible migration verified against PostgreSQL.
- Runtime-affecting changes pass a Docker build and startup check.
- A fresh clone can still start with `docker compose up --build`.
- Commits are focused and the working tree is clean.
- Pushed changes have green GitHub checks before handoff.
