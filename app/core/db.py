from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

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

Base = declarative_base()

def get_db():
    """Returns a database session generator for use in FastAPI dependencies."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
