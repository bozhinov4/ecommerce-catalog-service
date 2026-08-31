# Development Guidelines

## Scope

- This repository is a FastAPI and PostgreSQL service managed with `uv`.
- Use only `mcp__github-python__*` for GitHub platform operations.
- Do not use Jira, Confluence, Compass, Atlassian, or `-dsm` namespaces.

## Workflow

- Add dependencies with `uv add`; never edit lockfile contents manually.
- Run commands through `uv run`.
- Keep commits small with short, outcome-focused subjects.
- Add tests for every behavior change.
- Keep API routes thin and business/query logic independently testable.

## Quality Gates

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --cov --cov-report=term-missing
```
