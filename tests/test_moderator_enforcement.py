import sys
from pathlib import Path

# Ensure project root is in sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
import models

# ---------- Fixtures ----------

@pytest.fixture(scope="function")
def test_engine():
    """Create a fresh in‑memory SQLite engine for each test function."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine):
    """SQLAlchemy session bound to the test engine."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client(test_engine, db_session):
    """FastAPI TestClient that uses the test DB session via dependency override.
    Restores any previous dependency override after the test.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    # Save any existing override (e.g., from CSP tests)
    previous_override = app.dependency_overrides.get(get_db)
    # Apply the test‑specific override
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    # Restore the prior override (or remove if none existed)
    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override

@pytest.fixture(scope="function")
def sample_data(db_session):
    """Create a user, a moderator, a tweet (assigned), and the assignment.
    Returns a dict of IDs for use in tests.
    """
    # Author user
    author = models.User(twitter_user_id="u_123", handle="author_user")
    db_session.add(author)
    db_session.commit()
    db_session.refresh(author)

    # Moderator
    mod = models.Moderator(name="Mod One", max_capacity=5, role="general", languages="en")
    db_session.add(mod)
    db_session.commit()
    db_session.refresh(mod)

    # Tweet
    tweet = models.Tweet(
        tweet_id_str="tweet_001",
        text="sample tweet content",
        author_id=author.id,
        status="assigned",
    )
    db_session.add(tweet)
    db_session.commit()
    db_session.refresh(tweet)

    # Assignment linking tweet and moderator
    assignment = models.ModeratorAssignment(tweet_id=tweet.id, moderator_id=mod.id)
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    return {
        "author_id": author.id,
        "moderator_id": mod.id,
        "tweet_id": tweet.id,
    }

# ---------- Tests ----------

def test_warning_reply_integration(client, sample_data, db_session):
    payload = {
        "tweet_id": sample_data["tweet_id"],
        "moderator_id": sample_data["moderator_id"],
        "verdict": "mild_hate",
        "action_taken": "warning_reply",
    }
    response = client.post("/api/moderator-action", json=payload)
    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json["enforcement_status"] == "simulated"

    # Verify DB side‑effects
    assert db_session.query(models.ActionLog).count() == 1
    warning = db_session.query(models.Warning).first()
    assert warning is not None
    assert warning.user_id == sample_data["author_id"]
    assert warning.tweet_id == sample_data["tweet_id"]
    assert db_session.query(models.StrikeLog).count() == 0

def test_delete_integration(client, sample_data, db_session):
    payload = {
        "tweet_id": sample_data["tweet_id"],
        "moderator_id": sample_data["moderator_id"],
        "verdict": "hate_speech",
        "action_taken": "delete",
    }
    response = client.post("/api/moderator-action", json=payload)
    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json["enforcement_status"] == "simulated"

    assert db_session.query(models.ActionLog).count() == 1
    assert db_session.query(models.Warning).count() == 0
    assert db_session.query(models.StrikeLog).count() == 0

def test_delete_and_strike_integration(client, sample_data, db_session):
    payload = {
        "tweet_id": sample_data["tweet_id"],
        "moderator_id": sample_data["moderator_id"],
        "verdict": "severe_threat",
        "action_taken": "delete_and_strike",
    }
    response = client.post("/api/moderator-action", json=payload)
    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json["enforcement_status"] == "simulated"

    assert db_session.query(models.ActionLog).count() == 1
    strike = db_session.query(models.StrikeLog).first()
    assert strike is not None
    assert strike.user_id == sample_data["author_id"]
    assert strike.tweet_id == sample_data["tweet_id"]
    assert db_session.query(models.Warning).count() == 0

def test_no_action_integration(client, sample_data, db_session):
    payload = {
        "tweet_id": sample_data["tweet_id"],
        "moderator_id": sample_data["moderator_id"],
        "verdict": "clean",
        "action_taken": "no_action",
    }
    response = client.post("/api/moderator-action", json=payload)
    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json["enforcement_status"] == "no_action"

    assert db_session.query(models.ActionLog).count() == 1
    assert db_session.query(models.Warning).count() == 0
    assert db_session.query(models.StrikeLog).count() == 0

def test_unauthorized_moderator(client, sample_data, db_session):
    # Create a second moderator not assigned to the tweet
    other_mod = models.Moderator(name="Other Mod", max_capacity=5, role="general", languages="en")
    db_session.add(other_mod)
    db_session.commit()
    db_session.refresh(other_mod)

    payload = {
        "tweet_id": sample_data["tweet_id"],
        "moderator_id": other_mod.id,
        "verdict": "mild_hate",
        "action_taken": "warning_reply",
    }
    response = client.post("/api/moderator-action", json=payload)
    # Expect 403 because the tweet is not assigned to this moderator
    assert response.status_code == 403

    # No side‑effects should be recorded
    assert db_session.query(models.ActionLog).count() == 0
    assert db_session.query(models.Warning).count() == 0
    assert db_session.query(models.StrikeLog).count() == 0

def test_transaction_ordering(client, sample_data, db_session):
    """Ensure enforcement records are persisted within the same DB transaction."""
    payload = {
        "tweet_id": sample_data["tweet_id"],
        "moderator_id": sample_data["moderator_id"],
        "verdict": "mild_hate",
        "action_taken": "warning_reply",
    }
    response = client.post("/api/moderator-action", json=payload)
    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json["enforcement_status"] == "simulated"

    # After request completes, both ActionLog and Warning must be present
    assert db_session.query(models.ActionLog).count() == 1
    assert db_session.query(models.Warning).count() == 1
