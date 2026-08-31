"""Idempotent demo catalog seeding."""

from dataclasses import dataclass
from decimal import Decimal
from sys import stdout
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ecommerce_catalog_service.database import get_session_factory
from ecommerce_catalog_service.models import Category, Product


@dataclass(frozen=True, slots=True)
class CategorySeed:
    """Category values managed by the demo seed."""

    id: UUID
    name: str
    parent_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ProductSeed:
    """Product values managed by the demo seed."""

    id: UUID
    title: str
    description: str
    image: str
    sku: str
    price: Decimal
    category_id: UUID


@dataclass(frozen=True, slots=True)
class SeedSummary:
    """Counts produced by a demo seed run."""

    categories: int
    products: int
    categories_created: int
    products_created: int


ELECTRONICS_ID = UUID("10000000-0000-4000-8000-000000000001")
COMPUTERS_ID = UUID("10000000-0000-4000-8000-000000000002")
AUDIO_ID = UUID("10000000-0000-4000-8000-000000000003")
HOME_ID = UUID("10000000-0000-4000-8000-000000000004")
KITCHEN_ID = UUID("10000000-0000-4000-8000-000000000005")
OFFICE_ID = UUID("10000000-0000-4000-8000-000000000006")

CATEGORIES = (
    CategorySeed(ELECTRONICS_ID, "Electronics"),
    CategorySeed(COMPUTERS_ID, "Computers", ELECTRONICS_ID),
    CategorySeed(AUDIO_ID, "Audio", ELECTRONICS_ID),
    CategorySeed(HOME_ID, "Home & Living"),
    CategorySeed(KITCHEN_ID, "Kitchen", HOME_ID),
    CategorySeed(OFFICE_ID, "Office", HOME_ID),
)

PRODUCTS = (
    ProductSeed(
        UUID("20000000-0000-4000-8000-000000000001"),
        "Developer Ultrabook",
        "Lightweight 14-inch laptop with 32 GB RAM and a 1 TB SSD.",
        "https://placehold.co/800x600?text=Developer+Ultrabook",
        "DEMO-LAPTOP-001",
        Decimal("1599.00"),
        COMPUTERS_ID,
    ),
    ProductSeed(
        UUID("20000000-0000-4000-8000-000000000002"),
        "Portable Workstation",
        "High-performance laptop for demanding engineering workloads.",
        "https://placehold.co/800x600?text=Portable+Workstation",
        "DEMO-LAPTOP-002",
        Decimal("2399.99"),
        COMPUTERS_ID,
    ),
    ProductSeed(
        UUID("20000000-0000-4000-8000-000000000003"),
        "Noise-Cancelling Headphones",
        "Wireless over-ear headphones with adaptive noise cancellation.",
        "https://placehold.co/800x600?text=Wireless+Headphones",
        "DEMO-AUDIO-001",
        Decimal("249.90"),
        AUDIO_ID,
    ),
    ProductSeed(
        UUID("20000000-0000-4000-8000-000000000004"),
        "Compact Smart Speaker",
        "Room-filling sound in a compact voice-enabled speaker.",
        "https://placehold.co/800x600?text=Smart+Speaker",
        "DEMO-AUDIO-002",
        Decimal("89.50"),
        AUDIO_ID,
    ),
    ProductSeed(
        UUID("20000000-0000-4000-8000-000000000005"),
        "Burr Coffee Grinder",
        "Adjustable stainless-steel grinder for consistent coffee grounds.",
        "https://placehold.co/800x600?text=Coffee+Grinder",
        "DEMO-KITCHEN-001",
        Decimal("79.95"),
        KITCHEN_ID,
    ),
    ProductSeed(
        UUID("20000000-0000-4000-8000-000000000006"),
        "Insulated Travel Mug",
        "Leak-resistant reusable mug that keeps drinks warm for hours.",
        "https://placehold.co/800x600?text=Travel+Mug",
        "DEMO-KITCHEN-002",
        Decimal("24.99"),
        KITCHEN_ID,
    ),
    ProductSeed(
        UUID("20000000-0000-4000-8000-000000000007"),
        "Adjustable Desk Lamp",
        "Dimmable LED desk lamp with adjustable color temperature.",
        "https://placehold.co/800x600?text=Desk+Lamp",
        "DEMO-OFFICE-001",
        Decimal("45.00"),
        OFFICE_ID,
    ),
    ProductSeed(
        UUID("20000000-0000-4000-8000-000000000008"),
        "Ergonomic Office Chair",
        "Supportive mesh chair with adjustable lumbar support and armrests.",
        "https://placehold.co/800x600?text=Office+Chair",
        "DEMO-OFFICE-002",
        Decimal("349.00"),
        OFFICE_ID,
    ),
)


def _upsert_category(session: Session, seed: CategorySeed) -> bool:
    category = session.get(Category, seed.id)
    created = category is None
    if category is None:
        category = Category(id=seed.id)
        session.add(category)
    category.name = seed.name
    category.parent_id = seed.parent_id
    return created


def _upsert_product(session: Session, seed: ProductSeed) -> bool:
    product = session.scalar(select(Product).where(Product.sku == seed.sku))
    if product is None:
        product = session.get(Product, seed.id)
    created = product is None
    if product is None:
        product = Product(id=seed.id)
        session.add(product)
    product.title = seed.title
    product.description = seed.description
    product.image = seed.image
    product.sku = seed.sku
    product.price = seed.price
    product.category_id = seed.category_id
    return created


def seed_demo_catalog(session: Session) -> SeedSummary:
    """Create or restore the deterministic demo catalog in one transaction."""
    categories_created = sum(_upsert_category(session, seed) for seed in CATEGORIES)
    session.flush()
    products_created = sum(_upsert_product(session, seed) for seed in PRODUCTS)
    session.commit()

    categories = session.scalar(select(func.count()).select_from(Category)) or 0
    products = session.scalar(select(func.count()).select_from(Product)) or 0
    return SeedSummary(
        categories=categories,
        products=products,
        categories_created=categories_created,
        products_created=products_created,
    )


def main() -> None:
    """Seed the configured database and report the resulting catalog size."""
    with get_session_factory()() as session:
        summary = seed_demo_catalog(session)
    stdout.write(
        f"Demo catalog ready: {summary.categories} categories, "
        f"{summary.products} products "
        f"({summary.categories_created + summary.products_created} created).\n"
    )


if __name__ == "__main__":
    main()
