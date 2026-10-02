from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# --- TWEET SCHEMAS ---

class TweetIngestRequest(BaseModel):
    tweet_id_str: str
    text: str
    author_twitter_id: str
    author_handle: str

class TweetBase(BaseModel):
    tweet_id_str: str
    text: str
    author_id: int
    ai_category: Optional[str] = None
    confidence_score: Optional[float] = None
    status: str = "pending"

class TweetResponse(TweetBase):
    id: int
    created_at: datetime
    author_handle: Optional[str] = None

    class Config:
        from_attributes = True

# --- MODERATOR SCHEMAS ---

class ModeratorBase(BaseModel):
    name: str
    max_capacity: int = 5
    role: str = "general"
    languages: Optional[str] = None

class ModeratorResponse(ModeratorBase):
    id: int
    active_load: int

    class Config:
        from_attributes = True

# --- ACTION LOG SCHEMAS ---

class ModeratorActionRequest(BaseModel):
    tweet_id: int
    moderator_id: int
    verdict: str
    action_taken: str

class ActionLogBase(BaseModel):
    tweet_id: int
    moderator_id: int
    verdict: str
    action_taken: str

class ActionLogResponse(ActionLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
