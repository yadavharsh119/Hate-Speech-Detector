from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db

router = APIRouter(prefix="/api", tags=["Moderator"])

@router.get("/moderator-queue/{moderator_id}", response_model=list[schemas.TweetResponse])
def get_moderator_queue(moderator_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all tweets currently assigned to a specific moderator.
    Used by Member 4's Frontend Dashboard to populate the review queue.
    """
    tweets = (
        db.query(models.Tweet)
        .join(models.ModeratorAssignment, models.Tweet.id == models.ModeratorAssignment.tweet_id)
        .filter(models.ModeratorAssignment.moderator_id == moderator_id)
        .filter(models.Tweet.status == "assigned")
        .all()
    )
    return tweets

@router.post("/moderator-action", response_model=schemas.ActionLogResponse)
def submit_moderator_action(request: schemas.ModeratorActionRequest, db: Session = Depends(get_db)):
    """
    Process a moderator's decision (verdict and action) on a flagged tweet.
    """
    # 1. Verify the tweet exists and is currently in the assigned state
    tweet = db.query(models.Tweet).filter(models.Tweet.id == request.tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    if tweet.status != "assigned":
        raise HTTPException(status_code=400, detail="Tweet is not in 'assigned' state")

    # 2. Verify the moderator exists
    mod = db.query(models.Moderator).filter(models.Moderator.id == request.moderator_id).first()
    if not mod:
        raise HTTPException(status_code=404, detail="Moderator not found")

    # 3. Update the Tweet's status
    tweet.status = "reviewed"

    # 4. Create the Action Log entry to maintain a full audit trail
    action_log = models.ActionLog(
        tweet_id=request.tweet_id,
        moderator_id=request.moderator_id,
        verdict=request.verdict,
        action_taken=request.action_taken
    )
    db.add(action_log)

    # 5. Free up the moderator's capacity by decreasing their active load
    if mod.active_load > 0:
        mod.active_load -= 1

    # Save all changes safely in one transaction
    db.commit()
    db.refresh(action_log)

    # NOTE: Phase 6 will handle actually enforcing this action on Twitter 
    # (e.g., calling Twitter API to delete/warn) and updating User strike logs.

    return action_log
