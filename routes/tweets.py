from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db

router = APIRouter(prefix="/api", tags=["Tweets"])

@router.post("/ingest-tweet", response_model=schemas.TweetResponse)
def ingest_tweet(request: schemas.TweetIngestRequest, db: Session = Depends(get_db)):
    """
    Ingest a new tweet from the Twitter API.
    Creates the user if they don't exist, and stores the tweet as "pending".
    """
    # 1. Check if the author exists in our database, if not create them.
    user = db.query(models.User).filter(models.User.twitter_user_id == request.author_twitter_id).first()
    if not user:
        user = models.User(
            twitter_user_id=request.author_twitter_id, 
            handle=request.author_handle
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 2. Check if we've already ingested this exact tweet (avoid duplicates)
    existing_tweet = db.query(models.Tweet).filter(models.Tweet.tweet_id_str == request.tweet_id_str).first()
    if existing_tweet:
        raise HTTPException(status_code=400, detail="Tweet already exists in the system")

    # 3. Create the Tweet record
    new_tweet = models.Tweet(
        tweet_id_str=request.tweet_id_str,
        text=request.text,
        author_id=user.id,
        status="pending"
    )
    db.add(new_tweet)
    db.commit()
    db.refresh(new_tweet)

    # Note: In Phase 4, we will pass this `new_tweet.text` to Member 1's AI Classifier 
    # and then to Member 2's CSP. Right now, it just safely persists in the database.

    return new_tweet
