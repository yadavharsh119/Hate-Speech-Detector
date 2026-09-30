import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
import models

from sqlalchemy.pool import StaticPool

# Temporary SQLite DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_severe_tweet_assigned_to_senior_moderator(monkeypatch):
    db = TestingSessionLocal()
    # Add moderators
    mod1 = models.Moderator(name="General Mod", max_capacity=5, role="general", languages="en")
    mod2 = models.Moderator(name="Senior Mod", max_capacity=5, role="senior", languages="en")
    db.add(mod1)
    db.add(mod2)
    db.commit()
    db.close()

    def mock_predict_hate_speech(text):
        return {"predicted_category": "Severe", "confidence_score": 0.99, "flagged": True}

    monkeypatch.setattr("services.ai_classifier.predict_hate_speech", mock_predict_hate_speech)

    response = client.post("/api/ingest-tweet", json={
        "tweet_id_str": "123",
        "text": "Some text",
        "author_twitter_id": "u1",
        "author_handle": "user1"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "assigned"

    db = TestingSessionLocal()
    tweet = db.query(models.Tweet).filter(models.Tweet.tweet_id_str == "123").first()
    assignment = db.query(models.ModeratorAssignment).filter(models.ModeratorAssignment.tweet_id == tweet.id).first()
    assigned_mod = db.query(models.Moderator).filter(models.Moderator.id == assignment.moderator_id).first()
    assert assigned_mod.role == "senior"
    db.close()

def test_moderator_at_max_capacity_never_chosen(monkeypatch):
    db = TestingSessionLocal()
    mod1 = models.Moderator(name="Mod", max_capacity=1, active_load=1, role="general", languages="en")
    db.add(mod1)
    db.commit()
    db.close()

    def mock_predict_hate_speech(text):
        return {"predicted_category": "Mild", "confidence_score": 0.8, "flagged": True}

    monkeypatch.setattr("services.ai_classifier.predict_hate_speech", mock_predict_hate_speech)

    response = client.post("/api/ingest-tweet", json={
        "tweet_id_str": "124",
        "text": "Some text",
        "author_twitter_id": "u1",
        "author_handle": "user1"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "classified"

def test_no_available_moderators_no_crash(monkeypatch):
    # No moderators added to DB
    def mock_predict_hate_speech(text):
        return {"predicted_category": "Moderate", "confidence_score": 0.9, "flagged": True}

    monkeypatch.setattr("services.ai_classifier.predict_hate_speech", mock_predict_hate_speech)

    response = client.post("/api/ingest-tweet", json={
        "tweet_id_str": "125",
        "text": "Some text",
        "author_twitter_id": "u1",
        "author_handle": "user1"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "classified"

def test_language_matching_prefers_matching_moderator(monkeypatch):
    db = TestingSessionLocal()
    mod_en = models.Moderator(name="English Mod", max_capacity=5, role="general", languages="en")
    mod_es = models.Moderator(name="Spanish Mod", max_capacity=5, role="general", languages="es")
    db.add(mod_en)
    db.add(mod_es)
    db.commit()
    db.close()

    def mock_predict_hate_speech(text):
        return {"predicted_category": "Mild", "confidence_score": 0.8, "flagged": True}

    monkeypatch.setattr("services.ai_classifier.predict_hate_speech", mock_predict_hate_speech)

    response = client.post("/api/ingest-tweet", json={
        "tweet_id_str": "126",
        "text": "This is in espanol text",
        "author_twitter_id": "u1",
        "author_handle": "user1"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "assigned"

    db = TestingSessionLocal()
    tweet = db.query(models.Tweet).filter(models.Tweet.tweet_id_str == "126").first()
    assignment = db.query(models.ModeratorAssignment).filter(models.ModeratorAssignment.tweet_id == tweet.id).first()
    assigned_mod = db.query(models.Moderator).filter(models.Moderator.id == assignment.moderator_id).first()
    assert assigned_mod.languages == "es"
    db.close()
