import pytest
from unittest.mock import patch, MagicMock
from circuly import get_active_subscription, process_buyout, set_end_date, CirculyError, CirculyMultipleSubscriptionsError


FAKE_SUB = {
    "id": "order_sub_id",
    "status": "active",
    "item": {"name": "Igel Box (ab Geburt) | annual"},
}


@patch("circuly.requests.get")
def test_get_active_subscription_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"data": [FAKE_SUB]}

    sub_id, box_type = get_active_subscription("cus_123")
    assert sub_id == "order_sub_id"
    assert box_type == "igel"


@patch("circuly.requests.get")
def test_get_active_subscription_none_found(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"data": []}

    with pytest.raises(CirculyError, match="0 active subscriptions"):
        get_active_subscription("cus_123")


@patch("circuly.requests.get")
def test_get_active_subscription_multiple_raises(mock_get):
    """With 2+ active subs, raises CirculyMultipleSubscriptionsError — handle manually."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"data": [FAKE_SUB, FAKE_SUB]}

    with pytest.raises(CirculyMultipleSubscriptionsError):
        get_active_subscription("cus_123")


@patch("circuly.requests.post")
def test_process_buyout_success(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"status": "bought out"}

    process_buyout("sub_123")  # should not raise


@patch("circuly.requests.post")
def test_process_buyout_failure(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"message": "Buyout not allowed"}

    with pytest.raises(CirculyError, match="Buyout not allowed"):
        process_buyout("sub_123")


@patch("circuly.requests.put")
def test_set_end_date_success(mock_put):
    mock_put.return_value.status_code = 200
    mock_put.return_value.json.return_value = {"status": "pending_return"}

    set_end_date("sub_123", "2026-05-07")  # should not raise


def test_box_type_extraction_special():
    from circuly import extract_box_type, is_special_box
    assert extract_box_type("Fuchs Box | monthly") == "fuchs"
    assert is_special_box("fuchs") is True


def test_box_type_extraction_hase():
    from circuly import extract_box_type, is_special_box
    assert extract_box_type("Hase Box | annual") == "hase"
    assert is_special_box("hase") is False


def test_box_type_extraction_unknown():
    from circuly import extract_box_type, is_special_box
    assert extract_box_type("Unknown Product") == "other"
    assert is_special_box("other") is False


def test_box_type_extraction_waschbaer_not_special():
    """Waschbär must not match 'bär' (special) — longest match wins."""
    from circuly import extract_box_type, is_special_box
    assert extract_box_type("[+30M] Waschbär Box | annual") == "waschbär"
    assert is_special_box("waschbär") is False


def test_box_type_extraction_baer_is_special():
    """Plain Bär Box must still be special."""
    from circuly import extract_box_type, is_special_box
    assert extract_box_type("[+9M] Bär Box | annual") == "bär"
    assert is_special_box("bär") is True


def test_box_type_extraction_eichhoernchen_not_special():
    from circuly import extract_box_type, is_special_box
    assert extract_box_type("[+27M] Eichhörnchen Box | annual") == "eichhörnchen"
    assert is_special_box("eichhörnchen") is False
