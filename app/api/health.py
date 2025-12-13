"""
Health and system status endpoints
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.api import HealthResponse
from app.db import get_db

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check with database connectivity test"""
    
    # Test database connection
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "unhealthy",
        version="0.1.0",
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