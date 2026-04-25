from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.routers import auth, health
from app.common.config import settings
from app.common.utils import configure_logging, get_logger
from app.infrastructure.db import engine
from app.infrastructure.middlewares import add_middlewares

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Could not connect to database on startup: %s", exc)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

add_middlewares(app)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
