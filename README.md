# E-commerce Catalog Service

[![CI](https://github.com/bozhinov4/ecommerce-catalog-service/actions/workflows/ci.yml/badge.svg)](https://github.com/bozhinov4/ecommerce-catalog-service/actions/workflows/ci.yml)

A production-minded FastAPI service for managing products and hierarchical
categories. It provides complete CRUD APIs and composable product search by text,
SKU, price, and category tree.

## Assignment coverage

| Requirement | Implementation |
| --- | --- |
| Product | Title, description, image, unique SKU, price, and category |
| Category | Name and optional self-referencing parent |
| Product CRUD | Create, list, read, replace, and delete endpoints |
| Category CRUD | Create, list, read, replace, and guarded delete endpoints |
| Product search | Title/SKU, exact SKU, price range, and category tree |
| Search unit tests | Filters, hierarchy, sorting, pagination, and validation |

## Quick start

The only prerequisites are Docker and Docker Compose:

```bash
git clone https://github.com/bozhinov4/ecommerce-catalog-service.git
cd ecommerce-catalog-service
docker compose up --build
```

The container waits for PostgreSQL, applies all migrations, and starts the API.
For presentation convenience, Docker Compose also loads six categories and eight
products. The seed is idempotent, so restarts do not create duplicates.

- Interactive API documentation: <http://localhost:8000/docs>
- OpenAPI schema: <http://localhost:8000/openapi.json>
- Health check: <http://localhost:8000/health>

Stop the stack with `docker compose down`. Add `--volumes` only when you also want
to remove local database data.

## API

All catalog endpoints are versioned under `/api/v1`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/categories` | Create a category |
| `GET` | `/categories` | List categories |
| `GET` | `/categories/{id}` | Read a category |
| `PUT` | `/categories/{id}` | Replace a category |
| `DELETE` | `/categories/{id}` | Delete an empty category |
| `POST` | `/products` | Create a product |
| `GET` | `/products` | List products |
| `GET` | `/products/{id}` | Read a product |
| `PUT` | `/products/{id}` | Replace a product |
| `DELETE` | `/products/{id}` | Delete a product |
| `GET` | `/products/search` | Search and filter products |

### Search examples

Find products whose title or SKU contains `boots`:

```bash
curl 'http://localhost:8000/api/v1/products/search?q=boots'
```

Combine inclusive price bounds, a category tree, sorting, and pagination:

```bash
curl 'http://localhost:8000/api/v1/products/search?min_price=50&max_price=400&category_id=10000000-0000-4000-8000-000000000001&sort=price_asc'
```

Supported parameters:

| Parameter | Behavior |
| --- | --- |
| `q` | Case-insensitive partial title or SKU match |
| `sku` | Exact normalized SKU match |
| `min_price`, `max_price` | Inclusive price range |
| `category_id` | Category filter |
| `include_descendants` | Include the category subtree; defaults to `true` |
| `sort` | `title_asc`, `price_asc`, `price_desc`, or `newest` |
| `page`, `page_size` | Stable pagination with a maximum page size of 100 |

## Local Python workflow

Install [uv](https://docs.astral.sh/uv/) and start PostgreSQL, then run:

```bash
cp .env.example .env
uv sync --locked
uv run alembic upgrade head
uv run catalog-api
```

Initialize dependencies, the schema, and the demo catalog in one command:

```bash
make init
```

To refresh only the demo records later, run `make seed`. Existing records outside
the managed demo dataset are preserved. Production remains empty unless
`CATALOG_SEED_DEMO=true` is explicitly configured.

Useful commands:

```bash
make
make format
make lint
make test
make migrate
```

## Design decisions

- **FastAPI** keeps the assignment focused and generates OpenAPI documentation.
- **PostgreSQL** provides predictable production behavior for recursive category
  queries, decimal prices, constraints, and indexed case-insensitive search.
- **Purpose-built indexes** cover exact and partial SKU lookup, partial title search,
  category-price filtering, and standalone price ranges.
- **SQLAlchemy 2 and Alembic** keep persistence explicit and migrations reversible.
- **Synchronous database sessions** reduce incidental async complexity for this
  database-bound service while remaining safe under FastAPI's worker model.
- **Image URLs** keep media storage outside the catalog's carefully scoped boundary.
- **PUT replacements** make update validation deterministic; partial PATCH semantics
  can be added later if required.

The database enforces unique SKUs, positive prices, valid category references, and
restricted deletion. The service additionally prevents category cycles and deletion
of categories that still contain products or children.

## Deliberate scope

The assignment is intentionally kept small and production-minded:

- Authentication and authorization are deployment concerns and are not part of the
  requested catalog behavior.
- Product images are validated URLs; binary media storage belongs in an object store
  or dedicated media service.
- Updates use full `PUT` replacement. Partial `PATCH` behavior can be added without
  changing the existing contract.
- The health endpoint is a lightweight liveness check. A deployment-specific
  readiness endpoint can include database health when required.
- The repository publishes a deployable container but does not assume a particular
  cloud provider or production platform.

## Project structure

```text
src/ecommerce_catalog_service/
├── api/            # Versioned HTTP endpoints and dependencies
├── config.py       # Environment-backed settings
├── database.py     # Engine and request-scoped sessions
├── main.py         # Application factory and entry point
├── models.py       # SQLAlchemy models
├── schemas.py      # Pydantic contracts
├── seed.py         # Idempotent presentation data
└── services.py     # CRUD and search operations
migrations/         # Alembic revisions
tests/              # API, persistence, health, search, and seed tests
```

## Quality and delivery

Every code-related pull request runs formatting, linting, strict type checks, tests
with 100% statement and branch coverage, reversible migrations against PostgreSQL,
Compose validation, and a Docker build. Runtime changes on `main` and version tags
publish a multi-platform image to:

```bash
docker pull ghcr.io/bozhinov4/ecommerce-catalog-service:latest
```

The test suite specifically covers text/SKU matching, inclusive price bounds,
direct and recursive categories, combined filters, wildcard escaping, sorting,
pagination, invalid queries, and empty results. Fast unit tests use an isolated
in-memory database; CI separately validates the schema and complete migration cycle
against PostgreSQL 18.

## License

This project is available under the [MIT License](LICENSE).
