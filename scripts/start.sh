#!/bin/sh
set -eu

alembic upgrade head
exec uvicorn ecommerce_catalog_service.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers "${CATALOG_WORKERS:-2}"
