# E-commerce Catalog Service

A production-minded FastAPI service for managing and searching products and
hierarchical categories.

## Local development

```bash
cp .env.example .env
uv sync --locked
uv run catalog-api
```

Open <http://localhost:8000/docs> for the interactive API documentation or
<http://localhost:8000/health> for the health check.
