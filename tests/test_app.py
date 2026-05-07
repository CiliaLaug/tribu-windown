import pytest
from unittest.mock import patch, MagicMock
import json


@pytest.fixture
def client():
    import app as app_module
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


FAKE_CUSTOMER = {
    "page_id": "page-abc",
    "customer_id": "cus_123",
    "email": "test@example.com",
    "token": "validtoken",
    "freshdesk_ticket_id": 9001,
    "status": "pending",
}


# --- GET / ---

@patch("app.notion_log.get_customer_by_token", return_value=None)
def test_landing_invalid_token(mock_notion, client):
    resp = client.get("/?token=badtoken")
    assert resp.status_code == 200
    assert "Tribu Box" in resp.data.decode()
    # Should not show the choice page — neutral error
    assert "49,99" not in resp.data.decode()


@patch("app.notion_log.get_customer_by_token")
def test_landing_already_processed(mock_notion, client):
    customer = {**FAKE_CUSTOMER, "status": "keep"}
    mock_notion.return_value = customer
    resp = client.get("/?token=validtoken")
    assert b"bereits" in resp.data


@patch("app.notion_log.get_customer_by_token", return_value=FAKE_CUSTOMER)
def test_landing_pending_shows_page(mock_notion, client):
    resp = client.get("/?token=validtoken")
    assert resp.status_code == 200
    assert b"49,99" in resp.data


# --- POST /submit ---

@patch("app.notion_log.get_customer_by_token", return_value=None)
def test_submit_invalid_token(mock_notion, client):
    resp = client.post("/submit", json={"token": "bad", "choice": "keep"})
    assert resp.status_code == 400
    assert resp.json["ok"] is False


@patch("app.notion_log.get_customer_by_token")
def test_submit_already_processed(mock_notion, client):
    mock_notion.return_value = {**FAKE_CUSTOMER, "status": "keep"}
    resp = client.post("/submit", json={"token": "validtoken", "choice": "keep"})
    assert resp.status_code == 400


@patch("app.circuly.get_active_subscription", return_value=("sub_123", "hase"))
@patch("app.circuly.process_buyout")
@patch("app.freshdesk.reply_and_close")
@patch("app.notion_log.mark_processed")
@patch("app.notion_log.get_customer_by_token", return_value=FAKE_CUSTOMER)
def test_submit_keep_success(mock_notion, mock_mark, mock_fd, mock_buyout, mock_sub, client):
    resp = client.post("/submit", json={"token": "validtoken", "choice": "keep"})
    assert resp.status_code == 200
    assert resp.json["ok"] is True
    mock_buyout.assert_called_once_with("sub_123")
    mock_fd.assert_called_once()
    mock_mark.assert_called_once_with("page-abc", "keep")


@patch("app.circuly.get_active_subscription", return_value=("sub_123", "hase"))
@patch("app.circuly.set_end_date")
@patch("app.freshdesk.reply_and_close")
@patch("app.notion_log.mark_processed")
@patch("app.notion_log.get_customer_by_token", return_value=FAKE_CUSTOMER)
def test_submit_end_standard_box(mock_notion, mock_mark, mock_fd, mock_end, mock_sub, client):
    resp = client.post("/submit", json={"token": "validtoken", "choice": "end"})
    assert resp.status_code == 200
    assert resp.json["ok"] is True
    mock_end.assert_called_once()
    mock_fd.assert_called_once()
    mock_mark.assert_called_once_with("page-abc", "end")


@patch("app.circuly.get_active_subscription", return_value=("sub_123", "igel"))
@patch("app.freshdesk.reply_and_close")
@patch("app.notion_log.mark_error")
@patch("app.notion_log.get_customer_by_token", return_value=FAKE_CUSTOMER)
def test_submit_end_special_box(mock_notion, mock_error, mock_fd, mock_sub, client):
    resp = client.post("/submit", json={"token": "validtoken", "choice": "end"})
    assert resp.status_code == 200
    assert resp.json["ok"] is True
    mock_fd.assert_called_once()  # "keep/donate/recycle" email sent
    mock_error.assert_called_once_with("page-abc", "manual_review_end_subscription")


# --- POST /cron/fallback ---

def test_cron_no_secret(client):
    resp = client.post("/cron/fallback")
    assert resp.status_code == 403


def test_cron_wrong_secret(client):
    resp = client.post("/cron/fallback", headers={"X-Cron-Secret": "wrongsecret"})
    assert resp.status_code == 403
