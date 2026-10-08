import os

import models
from services.simulated_platform import SimulatedAdapter

# Credential env-var names required for the live Twitter adapter.
_TWITTER_ENV_VARS = (
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_SECRET",
)


def get_adapter(platform=None):
    """Return the appropriate platform adapter based on environment configuration.

    Selection order:
    1. Explicit *platform* argument ("twitter", "instagram", "simulated").
    2. MODERATION_PLATFORM environment variable (same values).
    3. Twitter-credentials check (all four vars present + tweepy importable).
    4. SimulatedAdapter (default / fallback).

    Calling with no args behaves exactly as before.
    """
    # Resolve effective platform: explicit arg beats env var
    effective = platform or os.environ.get("MODERATION_PLATFORM")

    if effective == "instagram":
        from services.instagram_client import InstagramAdapter  # noqa: PLC0415
        return InstagramAdapter()

    if effective == "twitter":
        try:
            from services.twitter_client import TwitterAdapter  # noqa: PLC0415
            return TwitterAdapter()
        except Exception:
            pass
        return SimulatedAdapter()

    if effective == "simulated":
        return SimulatedAdapter()

    # No explicit/env platform – legacy credential-sniffing path (unchanged behaviour)
    creds_present = all(os.environ.get(v) for v in _TWITTER_ENV_VARS)
    if creds_present:
        try:
            from services.twitter_client import TwitterAdapter  # noqa: PLC0415
            return TwitterAdapter()
        except Exception:
            pass
    return SimulatedAdapter()


class EnforcementService:
    """Phase 6 service translating moderator decisions into platform adapter calls and DB logging."""

    def __init__(self, adapter=None):
        self.adapter = adapter if adapter is not None else get_adapter()

    def execute(self, action_taken: str, tweet=None, db=None, verdict: str = None, *, platform=None) -> dict:
        """Execute a moderator action via platform adapter and record DB logs.

        Args:
            action_taken: Moderator action ("no_action", "warning_reply", "delete", "delete_and_strike").
            tweet: Tweet model instance or dict containing tweet and author info.
            db: SQLAlchemy session.
            verdict: Moderator verdict (e.g. "clean", "mild_hate", "hate_speech", "severe_threat").
            platform: Optional platform override passed to get_adapter (keyword-only).

        Returns:
            dict: Uniform result structure {platform, action, status, detail}.
        """
        # Support calling as EnforcementService.execute(...) as well as EnforcementService().execute(...)
        if isinstance(self, str):
            verdict = db
            db = tweet
            tweet = action_taken
            action_taken = self
            adapter = SimulatedAdapter()
        else:
            adapter = getattr(self, "adapter", None) or get_adapter(platform=platform)

        if action_taken == "no_action":
            return {
                "platform": "simulated",
                "action": "no_action",
                "status": "no_action",
                "detail": "No platform enforcement required.",
            }

        tweet_id_str = ""
        author_id = None
        tweet_pk = None

        if isinstance(tweet, dict):
            tweet_id_str = str(tweet.get("tweet_id_str") or tweet.get("id") or "")
            author_id = tweet.get("author_id")
            tweet_pk = tweet.get("id")
        elif tweet is not None:
            tweet_id_str = str(getattr(tweet, "tweet_id_str", None) or getattr(tweet, "id", ""))
            author_id = getattr(tweet, "author_id", None)
            tweet_pk = getattr(tweet, "id", None)

        try:
            if action_taken == "warning_reply":
                warning_message = (
                    f"Official Warning: Your post has been flagged for {verdict}."
                    if verdict
                    else "Official Warning: Your post violates community guidelines."
                )
                result = adapter.warn_reply(tweet_id_str, warning_message)
                if result.get("status") in ("simulated", "success"):
                    if db is not None and author_id is not None and tweet_pk is not None:
                        warning_record = models.Warning(
                            user_id=author_id,
                            tweet_id=tweet_pk,
                        )
                        db.add(warning_record)
                return result

            elif action_taken == "delete":
                result = adapter.delete_post(tweet_id_str)
                return result

            elif action_taken == "delete_and_strike":
                result = adapter.delete_post(tweet_id_str)
                if result.get("status") in ("simulated", "success"):
                    if db is not None and author_id is not None and tweet_pk is not None:
                        strike_record = models.StrikeLog(
                            user_id=author_id,
                            tweet_id=tweet_pk,
                        )
                        db.add(strike_record)
                return result

            else:
                return {
                    "platform": "simulated",
                    "action": action_taken,
                    "status": "error",
                    "detail": f"Unsupported action: {action_taken}",
                }

        except Exception as exc:
            return {
                "platform": "simulated",
                "action": action_taken,
                "status": "error",
                "detail": f"Enforcement failed: {str(exc)}",
            }
