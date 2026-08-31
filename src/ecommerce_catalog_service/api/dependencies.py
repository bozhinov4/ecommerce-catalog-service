"""Shared API dependencies."""

from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from ecommerce_catalog_service.database import get_db

DatabaseSession = Annotated[Session, Depends(get_db)]
Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]
