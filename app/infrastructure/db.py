from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.common.config import settings
from app.infrastructure.base import Base

engine = create_engine(
    settings.DB_URL,
    isolation_level=settings.ISOLATION_LEVEL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=0,
    pool_recycle=1800,
    pool_pre_ping=True,
    pool_timeout=30,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Returns a database session generator for use in FastAPI dependencies."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
