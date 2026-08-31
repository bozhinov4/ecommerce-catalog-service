"""Category CRUD endpoints."""

from uuid import UUID

from fastapi import APIRouter, Response, status

from ecommerce_catalog_service import services
from ecommerce_catalog_service.api.dependencies import DatabaseSession, Limit, Offset
from ecommerce_catalog_service.schemas import CategoryRead, CategoryWrite

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryWrite, session: DatabaseSession) -> CategoryRead:
    """Create a category."""
    return CategoryRead.model_validate(services.create_category(session, payload))


@router.get("")
def list_categories(
    session: DatabaseSession,
    offset: Offset = 0,
    limit: Limit = 50,
) -> list[CategoryRead]:
    """List categories with bounded pagination."""
    categories = services.list_categories(session, offset=offset, limit=limit)
    return [CategoryRead.model_validate(category) for category in categories]


@router.get("/{category_id}")
def get_category(category_id: UUID, session: DatabaseSession) -> CategoryRead:
    """Return one category."""
    return CategoryRead.model_validate(services.get_category(session, category_id))


@router.put("/{category_id}")
def replace_category(
    category_id: UUID,
    payload: CategoryWrite,
    session: DatabaseSession,
) -> CategoryRead:
    """Replace one category."""
    category = services.replace_category(session, category_id, payload)
    return CategoryRead.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: UUID, session: DatabaseSession) -> Response:
    """Delete an empty category."""
    services.delete_category(session, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
