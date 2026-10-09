from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# We use SQLite for the MVP as it requires no external setup.
# The database file will be created locally as 'hatespeech.db'.
SQLALCHEMY_DATABASE_URL = "sqlite:///./hatespeech.db"

# connect_args={"check_same_thread": False} is required for SQLite in FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get the DB session in FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_platform_column(bind=None):
    """Lightweight, idempotent migration: add the missing tweets.platform column.

    Base.metadata.create_all() only creates missing tables, so databases created
    before models.Tweet gained `platform` would fail at runtime.
    Existing rows are preserved and backfilled with the model default.
    Safe on fresh databases (no-op) and when the tweets table does not exist yet.
    """
    db_engine = bind if bind is not None else engine
    with db_engine.begin() as conn:
        columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(tweets)").fetchall()]
        if columns and "platform" not in columns:
            conn.exec_driver_sql(
                "ALTER TABLE tweets ADD COLUMN platform VARCHAR DEFAULT 'twitter'"
            )
