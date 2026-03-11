"""Health check route — like a /health endpoint in ASP.NET Core."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
async def health_check():
    return {"status": "healthy"}

