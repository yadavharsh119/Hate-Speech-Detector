from fastapi import FastAPI
from database import engine, Base
from routes import tweets, moderator

# Create the database tables
# This simple setup creates the 'hatespeech.db' file in the root directory
# and initializes all tables defined in models.py if they don't exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hate Speech Detector API",
    description="Backend pipeline connecting AI classification, CSP routing, and Moderator Dashboard",
    version="1.0.0"
)

app.include_router(tweets.router)
app.include_router(moderator.router)

@app.get("/")
def read_root():
    """
    Health check endpoint to verify the API is running.
    """
    return {
        "status": "online",
        "message": "Welcome to the Hate Speech Detector API"
    }
