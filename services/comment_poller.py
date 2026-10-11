"""Fallback polling of recent Instagram comments when webhooks do not deliver events."""
import asyncio
import os

import httpx
from fastapi import HTTPException

import schemas
from database import SessionLocal
from routes.tweets import ingest_tweet

DEFAULT_POLL_INTERVAL_SECONDS = 45
DEFAULT_POLL_BASE = "https://graph.instagram.com"


def _redact(message: str) -> str:
    """Never let the access token appear in any log line."""
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN") or ""
    if token:
        message = message.replace(token, "[REDACTED]")
    return message


async def _get_json(client: httpx.AsyncClient, url: str, params: dict):
    """GET url with query params; return parsed JSON or None after logging errors."""
    try:
        response = await client.get(url, params=params)
    except httpx.HTTPError as exc:
        print(f"[poller] request error: {_redact(str(exc))}")
        return None
    if response.status_code != 200:
        print(f"[poller] HTTP {response.status_code}: {_redact(response.text[:300])}")
        return None
    return response.json()


def _ingest_comment(comment: dict) -> bool:
    """Ingest one comment exactly like routes/webhook.py does (duplicate-safe)."""
    comment_id = comment.get("id")
    if not comment_id:
        return False
    username = comment.get("username") or "unknown"
    db = SessionLocal()
    try:
        ingest_tweet(
            schemas.TweetIngestRequest(
                tweet_id_str=comment_id,
                text=comment.get("text") or "",
                author_twitter_id=username,
                author_handle=username,
                platform="instagram",
            ),
            db,
        )
        return True
    except HTTPException as exc:
        if exc.status_code == 400:  # duplicate comment already in workflow
            return
        print(f"[poller] ingest error: {_redact(str(exc))}")
    except Exception as exc:
        print(f"[poller] ingest error: {_redact(str(exc))}")
    finally:
        db.close()
    return False


async def poll_once() -> None:
    counts = {"media": 0, "comments": 0, "new": 0}
    try:
        await _poll_once(counts)
    finally:
        print(
            "Poll cycle: {} media checked, {} comments seen, {} new".format(
                counts["media"], counts["comments"], counts["new"]
            )
        )


async def _poll_once(counts) -> None:
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    account = os.environ.get("IG_ACCOUNT_ID")
    if not token or not account:
        print("[poller] skipped: INSTAGRAM_ACCESS_TOKEN/IG_ACCOUNT_ID not set")
        return
    base = os.environ.get("IG_POLL_BASE", DEFAULT_POLL_BASE).rstrip("/")
    auth = {"access_token": token}
    async with httpx.AsyncClient(timeout=15.0) as client:
        media = await _get_json(
            client,
            f"{base}/{account}/media",
            {**auth, "fields": "id,timestamp", "limit": 5},
        )
        if not media:
            return
        for item in media.get("data", []):
            counts["media"] += 1
            media_id = item.get("id")
            if not media_id:
                continue
            comments = await _get_json(
                client,
                f"{base}/{media_id}/comments",
                {**auth, "fields": "id,text,username,timestamp", "limit": 25},
            )
            if not comments:
                continue
            for comment in comments.get("data", []):
                counts["comments"] += 1
                if await asyncio.to_thread(_ingest_comment, comment):
                    counts["new"] += 1


async def poll_loop() -> None:
    """Run poll_once forever; never dies on a transient error."""
    while True:
        try:
            print("Poll cycle start", flush=True)
            await poll_once()
        except Exception as exc:
            print(
                f"Poll cycle error: {type(exc).__name__}: {_redact(str(exc))}",
                flush=True,
            )
        try:
            interval = int(
                os.environ.get("POLL_INTERVAL_SECONDS", str(DEFAULT_POLL_INTERVAL_SECONDS))
            )
        except (ValueError, TypeError):
            interval = DEFAULT_POLL_INTERVAL_SECONDS
        await asyncio.sleep(interval)
