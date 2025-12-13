"""
Health and system status endpoints
"""
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check for production deployment"""
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )
        timestamp=datetime.utcnow()
    )


@router.get("/")
async def root():
    """Root endpoint redirect"""
    return {"message": "StreamFix Gateway", "docs": "/docs"}

@router.get("/ready")
async def readiness_check():
    """Readiness check - validates database connectivity"""
    from app.db import get_db_connection
    
    try:
        conn = await get_db_connection()
        await conn.fetchval("SELECT 1")
        await conn.close()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@router.get("/metrics")
async def basic_metrics():
    """Basic metrics endpoint for monitoring"""
    # TODO: Implement basic metrics
    return {
        "requests_total": 0,
        "requests_success": 0,
        "requests_failed": 0,
        "active_streams": 0
    }