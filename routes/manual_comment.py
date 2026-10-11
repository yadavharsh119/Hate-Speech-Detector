from uuid import uuid4
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

import schemas
from database import get_db
from routes.tweets import ingest_tweet

router = APIRouter(prefix="/api", tags=["Manual Comment"])


class ManualCommentRequest(BaseModel):
    text: str
    username: str = "demo_user"


@router.post("/submit-comment", response_model=schemas.TweetResponse)
def submit_comment(body: ManualCommentRequest, db: Session = Depends(get_db)):
    comment_id = "manual_" + uuid4().hex
    username = body.username or "demo_user"
    request = schemas.TweetIngestRequest(
        tweet_id_str=comment_id,
        text=body.text,
        author_twitter_id=username,
        author_handle=username,
        platform="instagram",
    )
    return ingest_tweet(request, db)
