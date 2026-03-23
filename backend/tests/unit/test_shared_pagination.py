from __future__ import annotations

from app.shared.pagination import PaginatedResponse, PaginationParams


def test_pagination_params_computes_offset() -> None:
    params = PaginationParams(page=3, page_size=25)

    assert params.offset == 50


def test_paginated_response_computes_total_pages() -> None:
    response = PaginatedResponse[int](
        items=[1, 2],
        total=21,
        page=2,
        page_size=10,
    )

    assert response.total_pages == 3


def test_paginated_response_handles_zero_page_size() -> None:
    response = PaginatedResponse[int](
        items=[],
        total=0,
        page=1,
        page_size=0,
    )

    assert response.total_pages == 0
