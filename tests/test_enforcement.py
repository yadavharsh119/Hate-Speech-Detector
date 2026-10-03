import sys
from pathlib import Path

# Ensure project root is in sys.path when running tests directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database import Base
import models
from services.enforcement import EnforcementService

# In-memory SQLite database isolated for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_tweet(db_session):
    author = models.User(twitter_user_id="u_999", handle="flagged_user")
    db_session.add(author)
    db_session.commit()
    db_session.refresh(author)

    tweet = models.Tweet(
        tweet_id_str="tweet_12345",
        text="Sample test content",
        author_id=author.id,
        status="assigned",
    )
    db_session.add(tweet)
    db_session.commit()
    db_session.refresh(tweet)
    return tweet


def test_no_action(db_session, sample_tweet):
    service = EnforcementService()
    result = service.execute("no_action", sample_tweet, db_session, verdict="clean")
    db_session.flush()

    assert result["platform"] == "simulated"
    assert result["action"] == "no_action"
    assert result["status"] == "no_action"
    assert "No platform enforcement required" in result["detail"]

    assert db_session.query(models.Warning).count() == 0
    assert db_session.query(models.StrikeLog).count() == 0


def test_warning_reply(db_session, sample_tweet):
    service = EnforcementService()
    result = service.execute("warning_reply", sample_tweet, db_session, verdict="mild_hate")
    db_session.flush()

    assert result["platform"] == "simulated"
    assert result["action"] == "warning_reply"
    assert result["status"] == "simulated"
    assert "A warning reply would have been sent" in result["detail"]

    warnings = db_session.query(models.Warning).all()
    assert len(warnings) == 1
    assert warnings[0].user_id == sample_tweet.author_id
    assert warnings[0].tweet_id == sample_tweet.id
    assert db_session.query(models.StrikeLog).count() == 0


def test_delete(db_session, sample_tweet):
    service = EnforcementService()
    result = service.execute("delete", sample_tweet, db_session, verdict="hate_speech")
    db_session.flush()

    assert result["platform"] == "simulated"
    assert result["action"] == "delete_post"
    assert result["status"] == "simulated"
    assert "would have been deleted" in result["detail"]

    assert db_session.query(models.StrikeLog).count() == 0
    assert db_session.query(models.Warning).count() == 0


def test_delete_and_strike(db_session, sample_tweet):
    service = EnforcementService()
    result = service.execute("delete_and_strike", sample_tweet, db_session, verdict="severe_threat")
    db_session.flush()

    assert result["platform"] == "simulated"
    assert result["action"] == "delete_post"
    assert result["status"] == "simulated"
    assert "would have been deleted" in result["detail"]

    strikes = db_session.query(models.StrikeLog).all()
    assert len(strikes) == 1
    assert strikes[0].user_id == sample_tweet.author_id
    assert strikes[0].tweet_id == sample_tweet.id
    assert db_session.query(models.Warning).count() == 0


def test_unsupported_action(db_session, sample_tweet):
    service = EnforcementService()
    result = service.execute("unknown_custom_action", sample_tweet, db_session, verdict="severe_threat")
    db_session.flush()

    assert result["platform"] == "simulated"
    assert result["action"] == "unknown_custom_action"
    assert result["status"] == "error"
    assert "Unsupported action" in result["detail"]

    assert db_session.query(models.Warning).count() == 0
    assert db_session.query(models.StrikeLog).count() == 0
