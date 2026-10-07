from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import case
import models
import schemas
from database import get_db
from services.enforcement import EnforcementService

VALID_VERDICTS = {"clean", "mild_hate", "hate_speech", "severe_threat"}
VALID_ACTIONS = {"no_action", "warning_reply", "delete", "delete_and_strike"}

router = APIRouter(prefix="/api", tags=["Moderator"])

@router.get("/moderator-queue/{moderator_id}", response_model=list[schemas.TweetResponse])
def get_moderator_queue(moderator_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all tweets currently assigned to a specific moderator.
    Used by Member 4's Frontend Dashboard to populate the review queue.
    """
    results = (
        db.query(models.Tweet, models.User)
        .join(models.ModeratorAssignment, models.Tweet.id == models.ModeratorAssignment.tweet_id)
        .join(models.User, models.Tweet.author_id == models.User.id)
        .filter(models.ModeratorAssignment.moderator_id == moderator_id)
        .filter(models.Tweet.status == "assigned")
        .all()
    )
    tweets = []
    for tweet, user in results:
        tweet.author_handle = user.handle
        tweets.append(tweet)
    return tweets

@router.post("/moderator-action", response_model=schemas.ActionLogResponse)
def submit_moderator_action(request: schemas.ModeratorActionRequest, db: Session = Depends(get_db)):
    """
    Process a moderator's decision (verdict and action) on a flagged tweet.
    """
    if request.verdict not in VALID_VERDICTS or request.action_taken not in VALID_ACTIONS:
        raise HTTPException(status_code=422, detail="Invalid verdict or action_taken")

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

    # Verify tweet is assigned to this moderator
    assignment = (
        db.query(models.ModeratorAssignment)
        .filter(
            models.ModeratorAssignment.tweet_id == request.tweet_id,
            models.ModeratorAssignment.moderator_id == request.moderator_id,
        )
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=403, detail="Tweet is not assigned to this moderator")

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

    # Check for queued tweets to assign
    sev_order = case(
        (models.Tweet.ai_category.in_(["Severe", "Severe Hate"]), 1),
        (models.Tweet.ai_category.in_(["Moderate", "Moderate Hate"]), 2),
        (models.Tweet.ai_category == "Mild", 3),
        else_=4,
    )
    queued_tweet = (
        db.query(models.Tweet)
        .filter(models.Tweet.status == "queued")
        .order_by(sev_order, models.Tweet.created_at.asc())
        .first()
    )
    if queued_tweet:
        from services.csp_assigner import assign_moderator
        assigned_mod_id = assign_moderator(queued_tweet.id, queued_tweet.ai_category, queued_tweet.text, db)
        if assigned_mod_id:
            queued_assignment = models.ModeratorAssignment(
                tweet_id=queued_tweet.id,
                moderator_id=assigned_mod_id,
            )
            db.add(queued_assignment)
            assigned_mod = db.query(models.Moderator).filter(models.Moderator.id == assigned_mod_id).first()
            if assigned_mod:
                assigned_mod.active_load += 1
            queued_tweet.status = "assigned"

    # Save all changes safely in one transaction
    # Phase 6: execute platform enforcement BEFORE committing so that
    # Warning / StrikeLog records added by EnforcementService are included
    # in the same transaction.
    enforcement_result = EnforcementService().execute(
        request.action_taken,
        tweet,
        db,
        request.verdict,
    )

    db.commit()
    db.refresh(action_log)

    return {
        "id": action_log.id,
        "tweet_id": action_log.tweet_id,
        "moderator_id": action_log.moderator_id,
        "verdict": action_log.verdict,
        "action_taken": action_log.action_taken,
        "timestamp": action_log.timestamp,
        "enforcement_status": enforcement_result["status"],
    }
