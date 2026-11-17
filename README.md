# Hate Speech Detector

A backend pipeline that ingests Instagram comments, classifies them for hate speech using machine learning, and assigns flagged content to moderators for review and action.

## What it does

The system receives Instagram comments through Meta webhooks or an automated polling fallback.
Each comment is processed by a text classifier to detect hate speech, offensive content, or threats.
Flagged comments are assigned to human moderators using constraint satisfaction rules based on language and workload capacity.
Moderators review items via API endpoints to log verdicts and trigger enforcement actions like warning replies or comment removal.

## How it works

1. Webhook intake: Meta sends a POST request with comment payloads to /webhook. The endpoint verifies the payload and extracts comment ID, text, and author handle.
2. Ingestion and deduplication: The comment is registered in SQLite under the tweets table. Duplicate comment IDs are ignored.
3. Machine learning classification: The text is sent to the classifier service. It runs inference via DistilBERT (or an alternate feedforward ANN). If trained model artifacts are absent, a deterministic rule-based fallback evaluates the text.
4. Triage: Content classified as safe is marked resolved. Content classified with mild, moderate, or severe severity is flagged for moderation.
5. Constraint-based routing (CSP): Flagged comments are routed using python-constraint solver. The solver matches comment language, verifies moderator active workload against max capacity, and enforces senior moderator assignment for severe threats.
6. Moderator queue and decision: The assigned moderator retrieves items via GET /api/moderator-queue/{moderator_id} and submits a verdict and action via POST /api/moderator-action.
7. Enforcement and audit log: The enforcement service executes platform actions (hide comment, reply warning) via the Instagram Graph API adapter (or simulated fallback). All actions, warnings, and strikes are recorded in the database.

## Tech stack

- Backend: Python 3, FastAPI, Uvicorn, Pydantic
- Database: SQLite, SQLAlchemy ORM
- Machine learning: DistilBERT (Hugging Face Transformers, PyTorch), TF-IDF + ANN (PyTorch)
- Moderator routing: python-constraint (Constraint Satisfaction Problem solver)
- External APIs: Meta Instagram Graph API (v21.0), Twitter/X API (Tweepy v2)
- Testing: pytest, HTTPX

## Project structure

```
.
├── backend/                  Backend model loading, config, and fallback classifier
├── docs/                     Project documentation and literature review
├── notebooks/                Jupyter notebook for model training and evaluation
├── routes/                   FastAPI route handlers (webhook, tweets, moderator, manual comment)
├── scripts/                  Helper scripts (seed moderators, ngrok tunnel, prototype server)
├── services/                 Business logic (classifier adapter, CSP assigner, poller, platform adapters)
├── tests/                    Test suite covering classification, CSP, enforcement, adapters, routes
├── csp_router.py             Core Constraint Satisfaction Problem assignment solver and priority buffer
├── database.py               SQLAlchemy database engine, session factory, and schema migrations
├── main.py                   FastAPI main application entry point and lifespan poller setup
├── models.py                 SQLAlchemy ORM models (User, Tweet, Moderator, ActionLog, etc.)
├── schemas.py                Pydantic validation schemas for API requests and responses
├── requirements.txt          Python package dependencies
├── .env                      Local environment variables (ignored by git)
└── .gitignore                Git ignore rules for secrets, databases, models, and cache
```

## Setup and run

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in a `.env` file:
```env
INSTAGRAM_ACCESS_TOKEN=
VERIFY_TOKEN=
MODEL_TYPE=
DISTILBERT_MODEL_PATH=
ANN_MODEL_DIR=
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
MODERATION_PLATFORM=
POLL_ENABLED=
POLL_INTERVAL_SECONDS=
```

3. Seed moderator profiles into the database:
```bash
python scripts/seed_moderator.py
```

4. Start the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```
Access interactive API documentation at `http://localhost:8000/docs`.

To run only the standalone classification API:
```bash
uvicorn backend.main:app --reload --port 8001
```

## How to run tests

Run the test suite with pytest:
```bash
python -m pytest tests/
```

Run tests with verbose output:
```bash
python -m pytest tests/ -v
```

Tests for the fine-tuned DistilBERT model are automatically skipped if weights are not present in the model directory.

## Current status and limitations

- Model weights are not tracked in git due to file size. Without downloading trained weights to `model/distilbert_final/` or `model/ann/`, the application runs with a deterministic keyword-based fallback classifier.
- Instagram enforcement relies on Meta Graph API tokens. Expired tokens prevent live comment deletion or replies; operations fall back to simulated responses.
- The web interface component files in the repository root are currently decoupled from the FastAPI backend and require integration.
- The database uses local SQLite, which is suitable for development and demonstration but lacks concurrency support for high-throughput production workloads.
- The language detection in moderator assignment defaults to English when language detection libraries are not active.
