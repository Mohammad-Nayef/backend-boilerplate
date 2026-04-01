from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.infrastructure.db import get_db

router = APIRouter(tags=["Health"])

@router.get("/health-check")
def health_check(db: Session = Depends(get_db)):
    """Simple up check that verifies database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "OK", "database": "Connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "Unhealthy", "database": str(e)}
        )
