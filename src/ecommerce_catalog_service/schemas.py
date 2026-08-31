"""Validated API request and response schemas."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from math import ceil
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    model_validator,
)

CategoryName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
]
ProductTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=240),
]
ProductDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=10_000),
]
Sku = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_upper=True,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    ),
]


class CategoryWrite(BaseModel):
    """Fields accepted when creating or replacing a category."""

    name: CategoryName
    parent_id: UUID | None = None


class CategoryRead(CategoryWrite):
    """Category representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class ProductWrite(BaseModel):
    """Fields accepted when creating or replacing a product."""

    title: ProductTitle
    description: ProductDescription
    image: HttpUrl
    sku: Sku
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category_id: UUID


class ProductRead(BaseModel):
    """Product representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    image: str
    sku: str
    price: Decimal
    category_id: UUID
    created_at: datetime
    updated_at: datetime


class ProductSort(StrEnum):
    """Supported product search orderings."""

    TITLE_ASC = "title_asc"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    NEWEST = "newest"


class ProductSearchParams(BaseModel):
    """Validated product search query parameters."""

    model_config = ConfigDict(extra="forbid")

    q: Annotated[
        str | None,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
    ] = None
    sku: Sku | None = None
    min_price: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )
    max_price: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )
    category_id: UUID | None = None
    include_descendants: bool = True
    sort: ProductSort = ProductSort.TITLE_ASC
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)

    @model_validator(mode="after")
    def validate_price_range(self) -> "ProductSearchParams":
        """Require the minimum price to be no greater than the maximum."""
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            msg = "min_price must be less than or equal to max_price"
            raise ValueError(msg)
        return self


class ProductPage(BaseModel):
    """Paginated product search response."""

    items: list[ProductRead]
    page: int
    page_size: int
    total: int
    pages: int

    @classmethod
    def create(
        cls,
        *,
        items: list[ProductRead],
        page: int,
        page_size: int,
        total: int,
    ) -> "ProductPage":
        """Build pagination metadata from a result set."""
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            pages=ceil(total / page_size) if total else 0,
        )
