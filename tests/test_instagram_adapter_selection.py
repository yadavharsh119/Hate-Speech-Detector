"""Tests for Instagram adapter selection in get_adapter."""
import os
import pytest
from services.enforcement import get_adapter


@pytest.fixture(autouse=True)
def clear_platform_env(monkeypatch):
    monkeypatch.delenv("MODERATION_PLATFORM", raising=False)
    for var in ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"]:
        monkeypatch.delenv(var, raising=False)
    yield


def test_env_var_selects_instagram(monkeypatch):
    """MODERATION_PLATFORM=instagram → InstagramAdapter returned."""
    monkeypatch.setenv("MODERATION_PLATFORM", "instagram")
    adapter = get_adapter()
    assert type(adapter).__name__ == "InstagramAdapter"


def test_explicit_platform_beats_env_var(monkeypatch):
    """Explicit platform='instagram' overrides MODERATION_PLATFORM=twitter."""
    monkeypatch.setenv("MODERATION_PLATFORM", "twitter")
    adapter = get_adapter(platform="instagram")
    assert type(adapter).__name__ == "InstagramAdapter"
