# Development Guidelines

## Scope

- This repository is a FastAPI and PostgreSQL service managed with `uv`.
- Use the `gh` CLI for GitHub platform operations.
- Do not use Jira, Confluence, Compass, or other Atlassian services.

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
- Keep API routes thin and business/query logic independently testable.
- Create an Alembic migration for every schema change and verify both upgrade and
  downgrade paths against PostgreSQL.
- Keep demo seeds idempotent and opt-in outside the local Docker Compose setup.
- Preserve backward compatibility unless a breaking API change is explicitly
  requested and documented.

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
