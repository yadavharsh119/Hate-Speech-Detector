import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
import models

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def test_submit_manual_comment():
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/submit-comment",
                json={"text": "This is a test comment", "username": "test_user"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["text"] == "This is a test comment"
            assert data["platform"] == "instagram"
            assert data["tweet_id_str"].startswith("manual_")
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)


def test_clean_comment_ends_up_resolved_with_no_assignment(monkeypatch):
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    mod = models.Moderator(name="General Mod", max_capacity=5, role="general", languages="en")
    db.add(mod)
    db.commit()
    db.close()

    def mock_predict_hate_speech(text):
        return {
            "predicted_category": "Clean",
            "confidence_score": 0.99,
            "flagged": False,
            "model_source": "test",
        }

    monkeypatch.setattr("services.ai_classifier.predict_hate_speech", mock_predict_hate_speech)

    csp_called = False

    def guard_assign_moderator(*args, **kwargs):
        nonlocal csp_called
        csp_called = True
        return mod.id

    monkeypatch.setattr("services.csp_assigner.assign_moderator", guard_assign_moderator)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/submit-comment",
                json={"text": "Have a wonderful day everyone!", "username": "test_user"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["ai_category"] == "Clean"
            assert data["status"] == "resolved"
            assert not csp_called

            db = TestingSessionLocal()
            tweet = db.query(models.Tweet).filter(models.Tweet.tweet_id_str == data["tweet_id_str"]).first()
            assert tweet is not None
            assert tweet.status == "resolved"

            assignments = (
                db.query(models.ModeratorAssignment)
                .filter(models.ModeratorAssignment.tweet_id == tweet.id)
                .all()
            )
            assert len(assignments) == 0
            db.close()
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)

