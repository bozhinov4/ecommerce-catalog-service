# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:0.12.7 AS uv

FROM python:3.14-slim-trixie AS builder

COPY --from=uv /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

FROM python:3.14-slim-trixie AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

RUN groupadd --system catalog && useradd --system --gid catalog catalog
COPY --from=builder --chown=catalog:catalog /app/.venv /app/.venv
COPY --chown=catalog:catalog alembic.ini ./
COPY --chown=catalog:catalog migrations ./migrations
COPY --chown=catalog:catalog scripts/start.sh ./scripts/start.sh
RUN chmod +x ./scripts/start.sh

USER catalog
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

ENTRYPOINT ["./scripts/start.sh"]
