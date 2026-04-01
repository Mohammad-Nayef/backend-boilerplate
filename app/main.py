from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.common.config import settings
from app.infrastructure.db import Base, engine
from app.api.routers import auth, health
from app.infrastructure.middlewares import add_middlewares
from app.common.utils import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Could not connect to database on startup: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

add_middlewares(app)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
