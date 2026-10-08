from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

# Must match what you just put into the Meta Dashboard
VERIFY_TOKEN = "hate_speech_detector"


@app.get("/webhook")
async def verify_webhook(request: Request):
    """Meta calls this GET endpoint once to verify your server URL."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@app.post("/webhook")
async def receive_webhook(request: Request):
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

    return {"status": "received"}
