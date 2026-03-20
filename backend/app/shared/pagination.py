from __future__ import annotations

from math import ceil
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, model_validator

T = TypeVar("T")


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = {"arbitrary_types_allowed": True}

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int = 0

    @model_validator(mode="after")
    def compute_pages(self) -> PaginatedResponse[T]:
        self.total_pages = ceil(self.total / self.page_size) if self.page_size > 0 else 0
        return self
