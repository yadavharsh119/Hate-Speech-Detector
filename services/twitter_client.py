"""Twitter/X platform adapter using Tweepy (X API v2).

This module is import-safe when Twitter credentials are absent.
No network request is made at import time or at construction time.
Credentials are read exclusively from environment variables.
"""

import os

import tweepy

from services.platform_base import PlatformAdapter

# Required credential environment-variable names.
_REQUIRED_ENV_VARS = (
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_SECRET",
)


def _get_credentials() -> dict | None:
    """Return a dict of credential values if all four are present, else None.

    Credentials are never printed or logged.
    """
    creds = {key: os.environ.get(key) for key in _REQUIRED_ENV_VARS}
    if all(creds.values()):
        return creds
    return None


def _build_client(creds: dict) -> tweepy.Client:
    """Construct and return an authenticated Tweepy Client (OAuth 1.0a user-context)."""
    return tweepy.Client(
        consumer_key=creds["TWITTER_API_KEY"],
        consumer_secret=creds["TWITTER_API_SECRET"],
        access_token=creds["TWITTER_ACCESS_TOKEN"],
        access_token_secret=creds["TWITTER_ACCESS_SECRET"],
    )


class TwitterAdapter(PlatformAdapter):
    """Live Twitter/X platform adapter backed by Tweepy Client (X API v2).

    Construction is credential-safe: if credentials are absent the adapter
    is constructed successfully but each method returns a structured error.
    No network request is made until a method is actually called.
    """

    def __init__(self) -> None:
        # Lazily resolved — we check credentials at call time, not here.
        self._client: tweepy.Client | None = None
        self._creds_checked: bool = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> tweepy.Client | None:
        """Return an authenticated Tweepy Client, or None if credentials are missing."""
        if not self._creds_checked:
            creds = _get_credentials()
            if creds is not None:
                self._client = _build_client(creds)
            self._creds_checked = True
        return self._client

    def _missing_creds_response(self, action: str) -> dict:
        return {
            "platform": "twitter",
            "action": action,
            "status": "error",
            "detail": "Twitter credentials are not configured. Set the required environment variables.",
        }

    # ------------------------------------------------------------------
    # PlatformAdapter interface
    # ------------------------------------------------------------------

    def delete_post(self, tweet_id_str: str) -> dict:
        """Delete a tweet by its string ID using X API v2."""
        try:
            client = self._get_client()
            if client is None:
                return self._missing_creds_response("delete_post")
            client.delete_tweet(tweet_id_str)
            return {
                "platform": "twitter",
                "action": "delete_post",
                "status": "success",
                "detail": f"Tweet {tweet_id_str} deleted.",
            }
        except Exception as exc:
            return {
                "platform": "twitter",
                "action": "delete_post",
                "status": "error",
                "detail": f"Failed to delete tweet: {type(exc).__name__}",
            }

    def warn_reply(self, tweet_id_str: str, message: str) -> dict:
        """Post a public warning reply to a tweet using X API v2."""
        try:
            client = self._get_client()
            if client is None:
                return self._missing_creds_response("warning_reply")
            client.create_tweet(
                text=message,
                in_reply_to_tweet_id=tweet_id_str,
            )
            return {
                "platform": "twitter",
                "action": "warning_reply",
                "status": "success",
                "detail": f"Warning reply posted to tweet {tweet_id_str}.",
            }
        except Exception as exc:
            return {
                "platform": "twitter",
                "action": "warning_reply",
                "status": "error",
                "detail": f"Failed to post warning reply: {type(exc).__name__}",
            }

    def warn_dm(self, author_platform_id: str, message: str) -> dict:
        """Send a direct warning message to a user via X API v2 DM."""
        try:
            client = self._get_client()
            if client is None:
                return self._missing_creds_response("warning_dm")
            client.create_direct_message(
                participant_id=author_platform_id,
                text=message,
            )
            return {
                "platform": "twitter",
                "action": "warning_dm",
                "status": "success",
                "detail": f"Warning DM sent to platform user {author_platform_id}.",
            }
        except Exception as exc:
            return {
                "platform": "twitter",
                "action": "warning_dm",
                "status": "error",
                "detail": f"Failed to send warning DM: {type(exc).__name__}",
            }
