from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

@app.get("/")
def read_root():
    """
    Health check endpoint to verify the API is running.
    """
    return {
        "status": "online",
        "message": "Welcome to the Hate Speech Detector API"
    }
