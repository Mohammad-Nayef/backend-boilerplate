from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/health-check")
def health_check():
    """Simple up check without DB call."""
    return {"status": "OK"}
