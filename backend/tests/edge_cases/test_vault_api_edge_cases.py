from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.edge_cases._api_helpers import auth_headers, register_and_login


@pytest.mark.asyncio
async def test_empty_vault_lists_return_empty_arrays(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens["access_token"])

    resumes = await client.get("/api/v1/vault/resumes", headers=headers)
    cover_letters = await client.get("/api/v1/vault/cover-letters", headers=headers)

    assert resumes.status_code == 200
    assert resumes.json() == []
    assert cover_letters.status_code == 200
    assert cover_letters.json() == []
