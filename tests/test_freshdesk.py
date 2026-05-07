import pytest
from unittest.mock import patch, MagicMock
from freshdesk import reply_and_close, FreshdeskError


@patch("freshdesk.requests.post")
@patch("freshdesk.requests.put")
def test_reply_and_close_success(mock_put, mock_post):
    mock_post.return_value.status_code = 201
    mock_put.return_value.status_code = 200

    reply_and_close(9001, "<p>Test body</p>")

    mock_post.assert_called_once()
    mock_put.assert_called_once()

    # Verify the reply was posted to correct URL
    post_url = mock_post.call_args[0][0]
    assert "9001" in post_url
    assert "reply" in post_url

    # Verify ticket was closed (status 5)
    put_body = mock_put.call_args[1]["json"]
    assert put_body["status"] == 5


@patch("freshdesk.requests.post")
def test_reply_failure_raises(mock_post):
    mock_post.return_value.status_code = 400
    mock_post.return_value.text = "Bad Request"

    with pytest.raises(FreshdeskError, match="Failed to reply"):
        reply_and_close(9001, "<p>body</p>")


@patch("freshdesk.requests.post")
@patch("freshdesk.requests.put")
def test_close_failure_raises(mock_put, mock_post):
    mock_post.return_value.status_code = 201
    mock_put.return_value.status_code = 500
    mock_put.return_value.text = "Server Error"

    with pytest.raises(FreshdeskError, match="Failed to close"):
        reply_and_close(9001, "<p>body</p>")
