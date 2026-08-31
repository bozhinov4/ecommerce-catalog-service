from decimal import Decimal
from typing import TYPE_CHECKING, cast
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from ecommerce_catalog_service import services
from ecommerce_catalog_service.database import get_db, get_session_factory
from ecommerce_catalog_service.models import Category, Product
from ecommerce_catalog_service.schemas import CategoryWrite

if TYPE_CHECKING:
    from sqlalchemy import Index, Table


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


def test_product_indexes_match_search_filters() -> None:
    product_table = cast("Table", Product.__table__)
    indexes: dict[str, Index] = {
        str(index.name): index
        for index in product_table.indexes
        if index.name is not None
    }

    assert {column.name for column in indexes["ix_products_price"].columns} == {"price"}
    assert indexes["ix_products_title_trgm"].dialect_options["postgresql"]["ops"] == {
        "title": "gin_trgm_ops"
    }
    assert indexes["ix_products_sku_trgm"].dialect_options["postgresql"]["ops"] == {
        "sku": "gin_trgm_ops"
    }


def test_create_rolls_back_integrity_errors(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commit_mock = Mock(
        side_effect=IntegrityError(
            "INSERT INTO products",
            {},
            ValueError("duplicate"),
        )
    )

    with session_factory() as session:
        rollback_mock = Mock(wraps=session.rollback)
        monkeypatch.setattr(session, "commit", commit_mock)
        monkeypatch.setattr(session, "rollback", rollback_mock)

        with pytest.raises(HTTPException) as error:
            services.create_category(session, CategoryWrite(name="Conflicting"))

    assert error.value.status_code == 409
    assert error.value.detail == "Category could not be created"
    rollback_mock.assert_called_once_with()
