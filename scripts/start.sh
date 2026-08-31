#!/bin/sh
set -eu

alembic upgrade head

case "${CATALOG_SEED_DEMO:-false}" in
    1 | true | TRUE | yes | YES) catalog-seed ;;
esac

exec uvicorn ecommerce_catalog_service.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers "${CATALOG_WORKERS:-2}"
