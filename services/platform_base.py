from abc import ABC, abstractmethod


class PlatformAdapter(ABC):
    """Abstract base class defining the platform-independent enforcement interface.

    Implementations must NOT raise platform/API exceptions to callers.
    Instead, they must return a uniform response dictionary:
    {
        "platform": "...",
        "action": "...",
        "status": "...",
        "detail": "..."
    }
    """

    @abstractmethod
    def delete_post(self, tweet_id_str: str) -> dict:
        """Delete a post on the platform.

        Implementations must catch platform/API exceptions and return
        the uniform response structure.
        """
        pass

    @abstractmethod
    def warn_reply(self, tweet_id_str: str, message: str) -> dict:
        """Post a public warning reply to a post.

        Implementations must catch platform/API exceptions and return
        the uniform response structure.
        """
        pass

    @abstractmethod
    def warn_dm(self, author_platform_id: str, message: str) -> dict:
        """Send a direct warning message to an author/user.

        Implementations must catch platform/API exceptions and return
        the uniform response structure.
        """
        pass
