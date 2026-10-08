import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
import pytest

from services.instagram_client import InstagramAdapter


@pytest.fixture
def adapter():
    return InstagramAdapter()


def test_delete_success(adapter, monkeypatch):
    monkeypatch.setenv("IG_ACCESS_TOKEN", "test_token")
    monkeypatch.setenv("IG_ACCOUNT_ID", "test_acc_id")
    monkeypatch.setenv("IG_API_BASE", "https://graph.facebook.com/v18.0")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("httpx.delete", return_value=mock_response) as mock_delete:
        res = adapter.delete_post("comment_123")
        assert res["platform"] == "instagram"
        assert res["action"] == "delete_post"
        assert res["status"] == "success"
        mock_delete.assert_called_once_with(
            "https://graph.facebook.com/v18.0/comment_123",
            params={"access_token": "test_token"},
        )


def test_reply_success(adapter, monkeypatch):
    monkeypatch.setenv("IG_ACCESS_TOKEN", "test_token")
    monkeypatch.setenv("IG_ACCOUNT_ID", "test_acc_id")
    monkeypatch.setenv("IG_API_BASE", "https://graph.facebook.com/v18.0")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("httpx.post", return_value=mock_response) as mock_post:
        res = adapter.warn_reply("comment_123", "Please refrain from hate speech.")
        assert res["platform"] == "instagram"
        assert res["action"] == "warn_reply"
        assert res["status"] == "success"
        mock_post.assert_called_once_with(
            "https://graph.facebook.com/v18.0/comment_123/replies",
            params={"access_token": "test_token"},
            json={"message": "Please refrain from hate speech."},
        )


def test_http_failure(adapter, monkeypatch):
    monkeypatch.setenv("IG_ACCESS_TOKEN", "test_token")
    monkeypatch.setenv("IG_ACCOUNT_ID", "test_acc_id")

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "400 Bad Request",
        request=MagicMock(),
        response=MagicMock(status_code=400),
    )

    with patch("httpx.delete", return_value=mock_response):
        res = adapter.delete_post("comment_123")
        assert res["platform"] == "instagram"
        assert res["action"] == "delete_post"
        assert res["status"] == "error"
        assert "Failed to delete post" in res["detail"]


def test_missing_creds(adapter, monkeypatch):
    monkeypatch.delenv("IG_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("IG_ACCOUNT_ID", raising=False)

    res_delete = adapter.delete_post("comment_123")
    assert res_delete["status"] == "error"
    assert "credentials are not configured" in res_delete["detail"]

    res_reply = adapter.warn_reply("comment_123", "Warning message")
    assert res_reply["status"] == "error"
    assert "credentials are not configured" in res_reply["detail"]


def test_warn_dm_not_supported(adapter):
    res = adapter.warn_dm("user_123", "Warning message")
    assert res["platform"] == "instagram"
    assert res["action"] == "warn_dm"
    assert res["status"] == "error"
    assert res["detail"] == "Instagram DMs only allowed if user messaged first; not supported"
