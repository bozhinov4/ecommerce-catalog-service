"""Optimize product search indexes."""

from collections.abc import Sequence

from alembic import op

revision: str = "20260831_02"
down_revision: str | None = "20260831_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Align trigram indexes with searches and index price-only filters."""
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_products_title_trgm")
        op.execute(
            "CREATE INDEX CONCURRENTLY ix_products_title_trgm "
            "ON products USING gin (title gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX CONCURRENTLY ix_products_sku_trgm "
            "ON products USING gin (sku gin_trgm_ops)"
        )
        op.execute("CREATE INDEX CONCURRENTLY ix_products_price ON products (price)")


def downgrade() -> None:
    """Restore the original title-only search index."""
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_products_price")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_products_sku_trgm")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_products_title_trgm")
        op.execute(
            "CREATE INDEX CONCURRENTLY ix_products_title_trgm "
            "ON products USING gin (lower(title) gin_trgm_ops)"
        )
