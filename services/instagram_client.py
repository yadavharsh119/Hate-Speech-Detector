"""Instagram platform adapter using httpx.

This module is import-safe when Instagram credentials are absent.
No network request is made at import time or at construction time.
Credentials are read exclusively from environment variables.
"""

import os
import httpx
from services.platform_base import PlatformAdapter

_REQUIRED_ENV_VARS = ("IG_ACCESS_TOKEN", "IG_ACCOUNT_ID")
_DEFAULT_BASE_URL = "https://graph.facebook.com/v18.0"


def _get_credentials() -> dict | None:
    creds = {key: os.environ.get(key) for key in _REQUIRED_ENV_VARS}
    if all(creds.values()):
        return creds
    return None


class InstagramAdapter(PlatformAdapter):
    """Live Instagram platform adapter backed by httpx."""

    def _missing_creds_response(self, action: str) -> dict:
        return {
            "platform": "instagram",
            "action": action,
            "status": "error",
            "detail": "Instagram credentials are not configured. Set the required environment variables.",
        }

    def delete_post(self, tweet_id_str: str) -> dict:
        """Delete a comment/post by its string ID using Instagram Graph API."""
        creds = _get_credentials()
        if creds is None:
            return self._missing_creds_response("delete_post")

        base_url = os.environ.get("IG_API_BASE", _DEFAULT_BASE_URL).rstrip("/")
        url = f"{base_url}/{tweet_id_str}"
        try:
            response = httpx.delete(url, params={"access_token": creds["IG_ACCESS_TOKEN"]})
            response.raise_for_status()
            return {
                "platform": "instagram",
                "action": "delete_post",
                "status": "success",
                "detail": f"Instagram post {tweet_id_str} deleted.",
            }
        except Exception as exc:
            return {
                "platform": "instagram",
                "action": "delete_post",
                "status": "error",
                "detail": f"Failed to delete post: {exc}",
            }

    def warn_reply(self, tweet_id_str: str, message: str) -> dict:
        """Post a public warning reply to a comment/post."""
        creds = _get_credentials()
        if creds is None:
            return self._missing_creds_response("warn_reply")

        base_url = os.environ.get("IG_API_BASE", _DEFAULT_BASE_URL).rstrip("/")
        url = f"{base_url}/{tweet_id_str}/replies"
        try:
            response = httpx.post(
                url,
                params={"access_token": creds["IG_ACCESS_TOKEN"]},
                json={"message": message},
            )
            response.raise_for_status()
            return {
                "platform": "instagram",
                "action": "warn_reply",
                "status": "success",
                "detail": f"Warning reply posted to comment {tweet_id_str}.",
            }
        except Exception as exc:
            return {
                "platform": "instagram",
                "action": "warn_reply",
                "status": "error",
                "detail": f"Failed to post warning reply: {exc}",
            }

    def warn_dm(self, author_platform_id: str, message: str) -> dict:
        """Attempt to send a direct warning message (unsupported on Instagram)."""
        return {
            "platform": "instagram",
            "action": "warn_dm",
            "status": "error",
            "detail": "Instagram DMs only allowed if user messaged first; not supported",
        }
