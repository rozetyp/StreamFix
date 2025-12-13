"""
StreamFix repair result retrieval endpoint
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.stream_processor import repair_results

router = APIRouter()

class RepairResult(BaseModel):
    """Repair result response model"""
    status: str  # "REPAIRED" or "PASSTHROUGH"
    original_json: str
    repaired_json: str
    parse_ok: bool
    error: Optional[str] = None

@router.get("/result/{request_id}")
async def get_repair_result(request_id: str) -> RepairResult:
    """
    Retrieve repair result for a completed streaming request
    
    Args:
        request_id: The request ID from X-StreamFix-Request-Id header
        
    Returns:
        RepairResult: The repair processing result
    """
    if request_id not in repair_results:
        raise HTTPException(status_code=404, detail="Request ID not found")
    
    result = repair_results[request_id]
    return RepairResult(**result)