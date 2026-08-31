"""Validated API request and response schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints

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
