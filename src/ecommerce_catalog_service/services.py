"""Catalog business operations."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import NoReturn
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from ecommerce_catalog_service.models import Category, Product
from ecommerce_catalog_service.schemas import (
    CategoryWrite,
    ProductSearchParams,
    ProductSort,
    ProductWrite,
)


@dataclass(frozen=True, slots=True)
class ProductSearchResult:
    """Products and total count returned by a search."""

    items: Sequence[Product]
    total: int


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


def _escape_like(value: str) -> str:
    """Escape user text before placing it in a LIKE pattern."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _category_filter(params: ProductSearchParams) -> ColumnElement[bool] | None:
    if params.category_id is None:
        return None
    if not params.include_descendants:
        return Product.category_id == params.category_id

    category_tree = (
        select(Category.id.label("id"))
        .where(Category.id == params.category_id)
        .cte("category_tree", recursive=True)
    )
    descendants = select(Category.id).join(
        category_tree,
        Category.parent_id == category_tree.c.id,
    )
    category_tree = category_tree.union_all(descendants)
    return Product.category_id.in_(select(category_tree.c.id))


def _apply_search_filters(
    statement: Select[tuple[Product]],
    params: ProductSearchParams,
) -> Select[tuple[Product]]:
    if params.q is not None:
        pattern = f"%{_escape_like(params.q)}%"
        statement = statement.where(
            or_(
                Product.title.ilike(pattern, escape="\\"),
                Product.sku.ilike(pattern, escape="\\"),
            )
        )
    if params.sku is not None:
        statement = statement.where(Product.sku == params.sku)
    if params.min_price is not None:
        statement = statement.where(Product.price >= params.min_price)
    if params.max_price is not None:
        statement = statement.where(Product.price <= params.max_price)
    category_filter = _category_filter(params)
    if category_filter is not None:
        statement = statement.where(category_filter)
    return statement


def _apply_search_order(
    statement: Select[tuple[Product]],
    sort: ProductSort,
) -> Select[tuple[Product]]:
    orderings = {
        ProductSort.TITLE_ASC: (Product.title.asc(), Product.id.asc()),
        ProductSort.PRICE_ASC: (Product.price.asc(), Product.id.asc()),
        ProductSort.PRICE_DESC: (Product.price.desc(), Product.id.asc()),
        ProductSort.NEWEST: (Product.created_at.desc(), Product.id.desc()),
    }
    return statement.order_by(*orderings[sort])


def search_products(
    session: Session,
    params: ProductSearchParams,
) -> ProductSearchResult:
    """Search products using composable, indexed filters."""
    filtered = _apply_search_filters(select(Product), params)
    total = session.scalar(select(func.count()).select_from(filtered.subquery())) or 0
    statement = (
        _apply_search_order(filtered, params.sort)
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    )
    return ProductSearchResult(items=session.scalars(statement).all(), total=total)
