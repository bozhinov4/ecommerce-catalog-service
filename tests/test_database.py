from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from ecommerce_catalog_service.database import get_db, get_session_factory
from ecommerce_catalog_service.models import Category, Product


def test_database_dependency_yields_session() -> None:
    session_iterator = get_db()

    session = next(session_iterator)

    assert isinstance(session, Session)
    session_iterator.close()


def test_catalog_models_keep_relationships() -> None:
    category = Category(name="Boots")
    product = Product(
        title="Control Boots",
        description="Firm-ground football boots.",
        image="https://example.com/boots.jpg",
        sku="BOOT-001",
        price=Decimal("99.99"),
        category_id=uuid4(),
    )

    product.category = category

    assert product.category.name == "Boots"
    assert get_session_factory().kw["expire_on_commit"] is False
