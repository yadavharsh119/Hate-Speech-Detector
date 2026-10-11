import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio

import httpx

from services import comment_poller


class FakeResponse:
    def __init__(self, status_code, payload, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload


class FakeSession:
    def close(self):
        pass


def test_poll_once_ingests_comments_like_the_webhook(monkeypatch):
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "dummy_token")
    monkeypatch.setenv("IG_ACCOUNT_ID", "acct_1")
    monkeypatch.delenv("IG_POLL_BASE", raising=False)

    async def fake_get(self, url, params=None):
        assert params["access_token"] == "dummy_token"
        if url.endswith("/media"):
            assert url == "https://graph.instagram.com/acct_1/media"
            return FakeResponse(200, {"data": [{"id": "media_1"}]})
        return FakeResponse(
            200,
            {"data": [{"id": "c_1", "text": "hello there", "username": "user_1"}]},
        )

    captured = []

    def fake_ingest(request, db):
        captured.append(request)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    monkeypatch.setattr(comment_poller, "ingest_tweet", fake_ingest)
    monkeypatch.setattr(comment_poller, "SessionLocal", FakeSession)

    asyncio.run(comment_poller.poll_once())

    assert len(captured) == 1
    req = captured[0]
    assert req.tweet_id_str == "c_1"
    assert req.text == "hello there"
    assert req.author_twitter_id == "user_1"
    assert req.author_handle == "user_1"
    assert req.platform == "instagram"
