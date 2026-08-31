"""SQLAlchemy persistence models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy evaluates annotations.
from decimal import Decimal  # noqa: TC003 - SQLAlchemy evaluates annotations.
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ecommerce_catalog_service.database import Base


class TimestampMixin:
    """Provide creation and modification timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Category(TimestampMixin, Base):
    """Hierarchical product category."""

    __tablename__ = "categories"
    __table_args__ = (Index("ix_categories_parent_id", "parent_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
    )

    parent: Mapped[Category | None] = relationship(
        back_populates="children",
        remote_side="Category.id",
    )
    children: Mapped[list[Category]] = relationship(back_populates="parent")
    products: Mapped[list[Product]] = relationship(back_populates="category")


class Product(TimestampMixin, Base):
    """Product available in the catalog."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price > 0", name="ck_products_price_positive"),
        Index("ix_products_category_price", "category_id", "price"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image: Mapped[str] = mapped_column(String(2048), nullable=False)
    sku: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )

    category: Mapped[Category] = relationship(back_populates="products")
