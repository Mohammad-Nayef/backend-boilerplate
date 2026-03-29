from fastapi import FastAPI
from app.core.config import settings
from app.core.db import Base, engine
from app.api.routers import auth, health
from app.core.middlewares import add_middlewares

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
)

add_middlewares(app)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api")
