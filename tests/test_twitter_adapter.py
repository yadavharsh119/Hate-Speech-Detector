import os
import builtins
import types

import pytest

# Import modules under test
from services.twitter_client import TwitterAdapter
from services.enforcement import get_adapter

# Helper to create a dummy Tweepy client with mock methods
class DummyClient:
    def __init__(self):
        self.called = {}

    def delete_tweet(self, tweet_id):
        self.called["delete_tweet"] = tweet_id
        return {}

    def create_tweet(self, *, text, in_reply_to_tweet_id):
        self.called["create_tweet"] = {
            "text": text,
            "in_reply_to_tweet_id": in_reply_to_tweet_id,
        }
        return {}

    def create_direct_message(self, *, participant_id, text):
        self.called["create_direct_message"] = {
            "participant_id": participant_id,
            "text": text,
        }
        return {}

# Fixture that ensures no real credentials are present unless a test explicitly sets them
@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    for var in ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"]:
        monkeypatch.delenv(var, raising=False)
    yield

# ---------------------------------------------------------------------------
# Test 1 – delete_post success
# ---------------------------------------------------------------------------
def test_delete_post_success(monkeypatch):
    # Set dummy credentials so the adapter will attempt to build a client
    for var in ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"]:
        monkeypatch.setenv(var, "dummy")

    dummy = DummyClient()
    # Patch the Tweepy Client class to return our dummy instance
    monkeypatch.setattr("services.twitter_client.tweepy.Client", lambda *a, **k: dummy)

    adapter = TwitterAdapter()
    result = adapter.delete_post("12345")

    assert dummy.called.get("delete_tweet") == "12345"
    assert result["platform"] == "twitter"
    assert result["action"] == "delete_post"
    assert result["status"] == "success"

# ---------------------------------------------------------------------------
# Test 2 – warn_reply success
# ---------------------------------------------------------------------------
def test_warn_reply_success(monkeypatch):
    for var in ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"]:
        monkeypatch.setenv(var, "dummy")
    dummy = DummyClient()
    monkeypatch.setattr("services.twitter_client.tweepy.Client", lambda *a, **k: dummy)

    adapter = TwitterAdapter()
    result = adapter.warn_reply("tweet123", "Test warning message")

    called = dummy.called.get("create_tweet")
    assert called is not None
    assert called["text"] == "Test warning message"
    assert called["in_reply_to_tweet_id"] == "tweet123"
    assert result["platform"] == "twitter"
    assert result["action"] == "warning_reply"
    assert result["status"] == "success"

# ---------------------------------------------------------------------------
# Test 3 – warn_dm success
# ---------------------------------------------------------------------------
def test_warn_dm_success(monkeypatch):
    for var in ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"]:
        monkeypatch.setenv(var, "dummy")
    dummy = DummyClient()
    monkeypatch.setattr("services.twitter_client.tweepy.Client", lambda *a, **k: dummy)

    adapter = TwitterAdapter()
    result = adapter.warn_dm("user123", "Direct warning")

    called = dummy.called.get("create_direct_message")
    assert called is not None
    assert called["participant_id"] == "user123"
    assert called["text"] == "Direct warning"
    assert result["platform"] == "twitter"
    assert result["action"] == "warning_dm"
    assert result["status"] == "success"

# ---------------------------------------------------------------------------
# Test 4 – missing credentials
# ---------------------------------------------------------------------------
def test_missing_credentials(monkeypatch):
    # Ensure no env vars are set (handled by fixture)
    adapter = TwitterAdapter()
    result = adapter.delete_post("any-id")
    assert result["platform"] == "twitter"
    assert result["action"] == "delete_post"
    assert result["status"] == "error"
    # Detail should mention missing credentials but not contain any secret values
    assert "credentials" in result["detail"].lower()

# ---------------------------------------------------------------------------
# Test 5 – API failure handling
# ---------------------------------------------------------------------------
def test_api_failure_handling(monkeypatch):
    for var in ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"]:
        monkeypatch.setenv(var, "dummy")
    dummy = DummyClient()
    # Make delete_tweet raise an exception
    def raise_exc(*args, **kwargs):
        raise RuntimeError("API failure")
    dummy.delete_tweet = raise_exc
    monkeypatch.setattr("services.twitter_client.tweepy.Client", lambda *a, **k: dummy)

    adapter = TwitterAdapter()
    result = adapter.delete_post("fail-id")
    assert result["platform"] == "twitter"
    assert result["action"] == "delete_post"
    assert result["status"] == "error"
    # Ensure the detail does not leak credentials – we only check the string does not contain the dummy value
    assert "dummy" not in result["detail"].lower()

# ---------------------------------------------------------------------------
# Test 6 – adapter selection without credentials (fallback to SimulatedAdapter)
# ---------------------------------------------------------------------------
def test_get_adapter_without_credentials(monkeypatch):
    # No env vars (fixture clears them)
    adapter = get_adapter()
    assert type(adapter).__name__ == "SimulatedAdapter"

# ---------------------------------------------------------------------------
# Test 7 – adapter selection with credentials (returns TwitterAdapter)
# ---------------------------------------------------------------------------
def test_get_adapter_with_credentials(monkeypatch):
    for var in ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"]:
        monkeypatch.setenv(var, "dummy")
    dummy = DummyClient()
    monkeypatch.setattr("services.twitter_client.tweepy.Client", lambda *a, **k: dummy)
    adapter = get_adapter()
    assert type(adapter).__name__ == "TwitterAdapter"
    # Verify that the returned adapter can successfully call a method without raising
    result = adapter.delete_post("test-id")
    assert result["status"] == "success"
