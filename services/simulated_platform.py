from services.platform_base import PlatformAdapter


class SimulatedAdapter(PlatformAdapter):
    """Simulated platform adapter for testing and safe offline enforcement."""

    def delete_post(self, tweet_id_str: str) -> dict:
        return {
            "platform": "simulated",
            "action": "delete_post",
            "status": "simulated",
            "detail": f"Post {tweet_id_str} would have been deleted.",
        }

    def warn_reply(self, tweet_id_str: str, message: str) -> dict:
        return {
            "platform": "simulated",
            "action": "warning_reply",
            "status": "simulated",
            "detail": f"A warning reply would have been sent to post {tweet_id_str}: {message}",
        }

    def warn_dm(self, author_platform_id: str, message: str) -> dict:
        return {
            "platform": "simulated",
            "action": "warning_dm",
            "status": "simulated",
            "detail": f"A warning DM would have been sent to platform user {author_platform_id}: {message}",
        }
