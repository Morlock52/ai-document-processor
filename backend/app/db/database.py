from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    # Verify connections before handing them out — prevents stale connection errors
    pool_pre_ping=True,
    # Enough headroom for concurrent requests per worker
    pool_size=10,
    max_overflow=20,
    # Recycle connections after 30 minutes to avoid hitting server-side timeouts
    pool_recycle=1800,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()