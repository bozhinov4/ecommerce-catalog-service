"""Product CRUD endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from ecommerce_catalog_service import services
from ecommerce_catalog_service.api.dependencies import DatabaseSession, Limit, Offset
from ecommerce_catalog_service.schemas import (
    ProductPage,
    ProductRead,
    ProductSearchParams,
    ProductWrite,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductWrite, session: DatabaseSession) -> ProductRead:
    """Create a product."""
    return ProductRead.model_validate(services.create_product(session, payload))


@router.get("")
def list_products(
    session: DatabaseSession,
    offset: Offset = 0,
    limit: Limit = 50,
) -> list[ProductRead]:
    """List products with bounded pagination."""
    products = services.list_products(session, offset=offset, limit=limit)
    return [ProductRead.model_validate(product) for product in products]


@router.get("/search")
def search_products(
    session: DatabaseSession,
    params: Annotated[ProductSearchParams, Query()],
) -> ProductPage:
    """Search and filter products."""
    result = services.search_products(session, params)
    return ProductPage.create(
        items=[ProductRead.model_validate(product) for product in result.items],
        page=params.page,
        page_size=params.page_size,
        total=result.total,
    )


@router.get("/{product_id}")
def get_product(product_id: UUID, session: DatabaseSession) -> ProductRead:
    """Return one product."""
    return ProductRead.model_validate(services.get_product(session, product_id))


@router.put("/{product_id}")
def replace_product(
    product_id: UUID,
    payload: ProductWrite,
    session: DatabaseSession,
) -> ProductRead:
    """Replace one product."""
    product = services.replace_product(session, product_id, payload)
    return ProductRead.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: UUID, session: DatabaseSession) -> Response:
    """Delete a product."""
    services.delete_product(session, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
