from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from ecommerce_catalog_service import seed
from ecommerce_catalog_service.models import Category, Product
from ecommerce_catalog_service.seed import CATEGORIES, PRODUCTS, seed_demo_catalog


def test_demo_seed_is_idempotent_and_restores_data(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        first = seed_demo_catalog(session)
        product = session.scalar(
            select(Product).where(Product.sku == "DEMO-LAPTOP-001")
        )
        assert product is not None
        product.price = Decimal("1.00")
        session.commit()

        second = seed_demo_catalog(session)
        restored_product = session.scalar(
            select(Product).where(Product.sku == "DEMO-LAPTOP-001")
        )

        assert first.categories_created == len(CATEGORIES)
        assert first.products_created == len(PRODUCTS)
        assert second.categories_created == 0
        assert second.products_created == 0
        assert restored_product is not None
        assert restored_product.price == Decimal("1599.00")
        assert session.scalar(select(func.count()).select_from(Category)) == len(
            CATEGORIES
        )
        assert session.scalar(select(func.count()).select_from(Product)) == len(
            PRODUCTS
        )


def test_demo_seed_preserves_unmanaged_records(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        session.add(Category(name="User category"))
        session.commit()

        summary = seed_demo_catalog(session)

        assert summary.categories == len(CATEGORIES) + 1
        assert (
            session.scalar(
                select(func.count())
                .select_from(Category)
                .where(Category.name == "User category")
            )
            == 1
        )


def test_seed_command_reports_summary(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(seed, "get_session_factory", lambda: session_factory)

    seed.main()

    assert capsys.readouterr().out == (
        "Demo catalog ready: 6 categories, 8 products (14 created).\n"
    )
