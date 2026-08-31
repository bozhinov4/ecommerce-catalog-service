"""Catalog business operations."""

from collections.abc import Sequence
from typing import NoReturn
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ecommerce_catalog_service.models import Category, Product
from ecommerce_catalog_service.schemas import CategoryWrite, ProductWrite


def _not_found(resource: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} not found",
    )


def _conflict(detail: str) -> NoReturn:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def _commit(session: Session, *, conflict_detail: str) -> None:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        _conflict(conflict_detail)


def get_category(session: Session, category_id: UUID) -> Category:
    """Return a category or raise a not-found response."""
    category = session.get(Category, category_id)
    if category is None:
        _not_found("Category")
    return category


def list_categories(session: Session, *, offset: int, limit: int) -> Sequence[Category]:
    """Return categories in stable name and identifier order."""
    statement = (
        select(Category)
        .order_by(Category.name, Category.id)
        .offset(offset)
        .limit(limit)
    )
    return session.scalars(statement).all()


def _validate_parent(
    session: Session,
    *,
    category_id: UUID | None,
    parent_id: UUID | None,
) -> Category | None:
    if parent_id is None:
        return None
    if parent_id == category_id:
        _conflict("A category cannot be its own parent")

    parent = get_category(session, parent_id)
    current: Category | None = parent
    while current is not None:
        if current.id == category_id:
            _conflict("A category cannot be moved below one of its descendants")
        current = current.parent
    return parent


def create_category(session: Session, payload: CategoryWrite) -> Category:
    """Create a category after validating its parent."""
    _validate_parent(session, category_id=None, parent_id=payload.parent_id)
    category = Category(name=payload.name, parent_id=payload.parent_id)
    session.add(category)
    _commit(session, conflict_detail="Category could not be created")
    session.refresh(category)
    return category


def replace_category(
    session: Session,
    category_id: UUID,
    payload: CategoryWrite,
) -> Category:
    """Replace a category while preventing hierarchy cycles."""
    category = get_category(session, category_id)
    _validate_parent(
        session,
        category_id=category_id,
        parent_id=payload.parent_id,
    )
    category.name = payload.name
    category.parent_id = payload.parent_id
    _commit(session, conflict_detail="Category could not be updated")
    session.refresh(category)
    return category


def delete_category(session: Session, category_id: UUID) -> None:
    """Delete an unused category."""
    category = get_category(session, category_id)
    has_children = session.scalar(
        select(Category.id).where(Category.parent_id == category_id).limit(1)
    )
    has_products = session.scalar(
        select(Product.id).where(Product.category_id == category_id).limit(1)
    )
    if has_children is not None or has_products is not None:
        _conflict("Category must be empty before it can be deleted")
    session.delete(category)
    _commit(session, conflict_detail="Category could not be deleted")


def get_product(session: Session, product_id: UUID) -> Product:
    """Return a product or raise a not-found response."""
    product = session.get(Product, product_id)
    if product is None:
        _not_found("Product")
    return product


def list_products(session: Session, *, offset: int, limit: int) -> Sequence[Product]:
    """Return products in stable title and identifier order."""
    statement = (
        select(Product).order_by(Product.title, Product.id).offset(offset).limit(limit)
    )
    return session.scalars(statement).all()


def _ensure_unique_sku(
    session: Session,
    *,
    sku: str,
    product_id: UUID | None = None,
) -> None:
    statement = select(Product.id).where(Product.sku == sku)
    if product_id is not None:
        statement = statement.where(Product.id != product_id)
    if session.scalar(statement.limit(1)) is not None:
        _conflict("A product with this SKU already exists")


def create_product(session: Session, payload: ProductWrite) -> Product:
    """Create a product in an existing category."""
    get_category(session, payload.category_id)
    _ensure_unique_sku(session, sku=payload.sku)
    product = Product(
        title=payload.title,
        description=payload.description,
        image=str(payload.image),
        sku=payload.sku,
        price=payload.price,
        category_id=payload.category_id,
    )
    session.add(product)
    _commit(session, conflict_detail="Product could not be created")
    session.refresh(product)
    return product


def replace_product(
    session: Session,
    product_id: UUID,
    payload: ProductWrite,
) -> Product:
    """Replace a product after validating category and SKU."""
    product = get_product(session, product_id)
    get_category(session, payload.category_id)
    _ensure_unique_sku(session, sku=payload.sku, product_id=product_id)
    product.title = payload.title
    product.description = payload.description
    product.image = str(payload.image)
    product.sku = payload.sku
    product.price = payload.price
    product.category_id = payload.category_id
    _commit(session, conflict_detail="Product could not be updated")
    session.refresh(product)
    return product


def delete_product(session: Session, product_id: UUID) -> None:
    """Delete a product."""
    product = get_product(session, product_id)
    session.delete(product)
    _commit(session, conflict_detail="Product could not be deleted")
