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
    # 1. Check if we've already ingested this exact tweet (avoid duplicates)
    existing_tweet = db.query(models.Tweet).filter(models.Tweet.tweet_id_str == request.tweet_id_str).first()
    if existing_tweet:
        raise HTTPException(status_code=400, detail="Tweet already exists in the system")

    # 2. Check if the author exists in our database, if not create them.
    user = db.query(models.User).filter(models.User.twitter_user_id == request.author_twitter_id).first()
    if not user:
        user = models.User(
            twitter_user_id=request.author_twitter_id, 
            handle=request.author_handle
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 3. Create the Tweet record initially as pending
    new_tweet = models.Tweet(
        tweet_id_str=request.tweet_id_str,
        text=request.text,
        author_id=user.id,
        platform=request.platform,
        status="pending"
    )
    db.add(new_tweet)
    db.flush() # Flush to get new_tweet.id without committing yet

    # 4. Member 1: AI Classification
    from services.ai_classifier import predict_hate_speech
    ai_result = predict_hate_speech(new_tweet.text)
    
    new_tweet.ai_category = ai_result["predicted_category"]
    new_tweet.confidence_score = ai_result["confidence_score"]
    
    # 5. Member 2: CSP Assignment (only if flagged)
    if ai_result["flagged"]:
        from services.csp_assigner import assign_moderator
        assigned_mod_id = assign_moderator(new_tweet.id, new_tweet.ai_category, new_tweet.text, db)
        
        if assigned_mod_id:
            # Create the assignment
            assignment = models.ModeratorAssignment(
                tweet_id=new_tweet.id,
                moderator_id=assigned_mod_id
            )
            db.add(assignment)
            
            # Update moderator's active load
            mod = db.query(models.Moderator).filter(models.Moderator.id == assigned_mod_id).first()
            mod.active_load += 1
            
            new_tweet.status = "assigned"
        else:
            # AI flagged it, but no moderators are available right now
            new_tweet.status = "queued"
    else:
        # Clean tweet, no review needed
        new_tweet.status = "classified"

    db.commit()
    db.refresh(new_tweet)

    return new_tweet