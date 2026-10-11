from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_submit_manual_comment():
    response = client.post(
        "/api/submit-comment",
        json={"text": "This is a test comment", "username": "test_user"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "This is a test comment"
    assert data["platform"] == "instagram"
    assert data["tweet_id_str"].startswith("manual_")
