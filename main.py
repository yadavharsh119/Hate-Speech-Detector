import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, ensure_platform_column
from routes import tweets, moderator, webhook
from routes import manual_comment

# Create the database tables
# This simple setup creates the 'hatespeech.db' file in the root directory
# and initializes all tables defined in models.py if they don't exist.
Base.metadata.create_all(bind=engine)

# Backfill support: add tweets.platform to databases created before models.py added it.
ensure_platform_column(engine)

@asynccontextmanager
async def lifespan(app):
    """Start the Instagram comment poller only when POLL_ENABLED=true."""
    task = None
    if os.environ.get("POLL_ENABLED", "").lower() == "true":
        import asyncio
        from services.comment_poller import poll_loop
        task = asyncio.create_task(poll_loop())
        print("Comment poller started, interval={}s".format(os.environ.get("POLL_INTERVAL_SECONDS", "45")))
    yield
    if task is not None:
        task.cancel()

app = FastAPI(
    title="Hate Speech Detector API",
    description="Backend pipeline connecting AI classification, CSP routing, and Moderator Dashboard",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8501",
        "http://127.0.0.1:5500"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tweets.router)
app.include_router(moderator.router)
app.include_router(webhook.router)
app.include_router(manual_comment.router)

@app.get("/")
def read_root():
    """
    Health check endpoint to verify the API is running.
    """
    return {
        "status": "online",
        "message": "Welcome to the Hate Speech Detector API"
    }
