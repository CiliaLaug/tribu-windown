import pytest
from unittest.mock import MagicMock, patch
from notion_log import get_customer_by_token, mark_processed, mark_error, get_pending_expired
from datetime import date, timedelta


FAKE_PAGE = {
    "id": "page-abc",
    "properties": {
        "customer_id": {"rich_text": [{"plain_text": "cus_123"}]},
        "email": {"email": "test@example.com"},
        "token": {"rich_text": [{"plain_text": "abc123token"}]},
        "freshdesk_ticket_id": {"number": 9001},
        "sent_at": {"date": {"start": "2026-04-20"}},
        "status": {"select": {"name": "pending"}},
        "error_detail": {"rich_text": []},
        "processed_at": {"date": None},
    }
}


@patch("notion_log.get_client")
def test_get_customer_by_token_found(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.databases.query.return_value = {"results": [FAKE_PAGE]}

    result = get_customer_by_token("abc123token")

    assert result["page_id"] == "page-abc"
    assert result["customer_id"] == "cus_123"
    assert result["freshdesk_ticket_id"] == 9001
    assert result["status"] == "pending"


@patch("notion_log.get_client")
def test_get_customer_by_token_not_found(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.databases.query.return_value = {"results": []}

    result = get_customer_by_token("bad_token")
    assert result is None


@patch("notion_log.get_client")
def test_mark_processed(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mark_processed("page-abc", "keep")

    mock_client.pages.update.assert_called_once()
    call_kwargs = mock_client.pages.update.call_args[1]
    assert call_kwargs["page_id"] == "page-abc"
    assert call_kwargs["properties"]["status"]["select"]["name"] == "keep"


@patch("notion_log.get_client")
def test_mark_error(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mark_error("page-abc", "circuly_failed")

    call_kwargs = mock_client.pages.update.call_args[1]
    assert call_kwargs["properties"]["status"]["select"]["name"] == "error"
    assert "circuly_failed" in str(call_kwargs["properties"]["error_detail"])


@patch("notion_log.get_client")
def test_get_pending_expired(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.databases.query.return_value = {"results": [FAKE_PAGE], "has_more": False}

    cutoff = date.today() - timedelta(days=14)
    results = get_pending_expired(cutoff)

    assert len(results) == 1
    mock_client.databases.query.assert_called_once()
