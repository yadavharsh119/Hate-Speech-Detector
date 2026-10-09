from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

import schemas
from database import get_db
from routes.tweets import ingest_tweet

router = APIRouter(tags=["Webhook"])

# Must match what you just put into the Meta Dashboard
VERIFY_TOKEN = "hate_speech_detector"


@router.get("/webhook")
async def verify_webhook(request: Request):
    """Meta calls this GET endpoint once to verify your server URL."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    """Meta pushes real-time comment events to this POST endpoint."""
    body = await request.json()
    print("📥 Incoming Webhook Payload:", body)

    if body.get("object") == "instagram":
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") == "comments":
                    value = change.get("value", {})
                    comment_id = value.get("id")
                    text = value.get("text")
                    username = value.get("from", {}).get("username", "unknown")

                    print(
                        f"🚨 New comment from @{username}: '{text}' (ID: {comment_id})"
                    )

                    if not comment_id:
                        continue

                    # Reuse the existing ingestion workflow from POST /api/ingest-tweet:
                    # dedupe, author upsert, predict_hate_speech(text), ai_category /
                    # confidence_score storage, and flagged -> CSP moderator assignment.
                    try:
                        ingested = ingest_tweet(
                            schemas.TweetIngestRequest(
                                tweet_id_str=comment_id,
                                text=text or "",
                                author_twitter_id=username,
                                author_handle=username,
                                platform="instagram",
                            ),
                            db,
                        )
                    except HTTPException as exc:
                        # Meta retries deliveries; a duplicate comment is not an error.
                        if exc.status_code != 400:
                            raise
                        print(f"ℹ️ Comment already in workflow (ID: {comment_id})")
                    else:
                        print(
                            f"🤖 AI Classification: category={ingested.ai_category}, "
                            f"confidence={ingested.confidence_score}, "
                            f"status={ingested.status}"
                        )

    return {"status": "received"}
