from __future__ import annotations

import base64
from datetime import UTC, datetime

import pytest

from app.integrations.gmail_client import GmailClient


def _encode_part(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("utf-8").rstrip("=")


@pytest.mark.asyncio
async def test_list_message_ids_filters_blank_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GmailClient()

    async def _fake_get_json(path: str, access_token: str, *, params=None):
        assert path == "/messages"
        assert access_token == "access-token"
        assert params == {"q": "label:important", "maxResults": 10}
        return {"messages": [{"id": "gmail-1"}, {"id": ""}, {}, {"id": "gmail-2"}]}

    monkeypatch.setattr(client, "_get_json", _fake_get_json)

    result = await client.list_message_ids(
        "access-token",
        query="label:important",
        max_results=10,
    )

    assert result == ["gmail-1", "gmail-2"]


@pytest.mark.asyncio
async def test_get_message_parses_nested_multipart_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = GmailClient()
    payload = {
        "id": "gmail-1",
        "threadId": "thread-1",
        "internalDate": str(int(datetime(2026, 3, 30, 12, 0, tzinfo=UTC).timestamp() * 1000)),
        "payload": {
            "headers": [
                {"name": "From", "value": "recruiting@acme-corp.com"},
                {"name": "To", "value": "owner@jobradar.dev"},
                {"name": "Subject", "value": "Interview Invitation"},
            ],
            "parts": [
                {
                    "mimeType": "multipart/alternative",
                    "parts": [
                        {
                            "mimeType": "text/plain",
                            "body": {"data": _encode_part("Plain text body")},
                        },
                        {
                            "mimeType": "text/html",
                            "body": {"data": _encode_part("<p>HTML body</p>")},
                        },
                    ],
                }
            ],
        },
    }

    async def _fake_get_json(path: str, access_token: str, *, params=None):
        assert path == "/messages/gmail-1"
        assert access_token == "access-token"
        assert params == {"format": "full"}
        return payload

    monkeypatch.setattr(client, "_get_json", _fake_get_json)

    message = await client.get_message("access-token", "gmail-1")

    assert message.message_id == "gmail-1"
    assert message.thread_id == "thread-1"
    assert message.sender == "recruiting@acme-corp.com"
    assert message.recipient == "owner@jobradar.dev"
    assert message.subject == "Interview Invitation"
    assert message.text_body == "Plain text body"
    assert message.html_body == "<p>HTML body</p>"
    assert message.received_at == datetime(2026, 3, 30, 12, 0, tzinfo=UTC)
