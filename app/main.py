from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.db import Base, engine
from app.api.routers import auth, health
from app.core.middlewares import add_middlewares

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logging.error(f"Could not connect to database on startup: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan
)

add_middlewares(app)

app.include_router(health.router)
app.include_router(auth.router)
