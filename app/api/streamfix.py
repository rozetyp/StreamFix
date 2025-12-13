"""
StreamFix test endpoint for JSON repair
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import json
from app.core.fsm import (
    PreprocessState, JsonFsmState, 
    preprocess_chunk, preprocess_finalize, preprocess_get_result,
    fsm_feed, fsm_finalize, fsm_result
)
from app.core.repair import safe_repair

router = APIRouter()

class RepairRequest(BaseModel):
    """Direct JSON repair request"""
    broken_json: str

class RepairTestResult(BaseModel):
    """Direct JSON repair test result"""
    success: bool
    original: str
    repaired: str
    valid_json: bool
    error: Optional[str] = None

@router.post("/test", response_model=RepairTestResult)
async def test_json_repair(request: RepairRequest) -> RepairTestResult:
    """
    Test JSON repair functionality directly without needing API keys
    
    This endpoint accepts broken JSON and returns the repaired version,
    allowing testing of the core StreamFix functionality for free.
    """
    try:
        broken_json = request.broken_json
        
        # Try to parse original (should fail)
        original_valid = True
        try:
            json.loads(broken_json)
        except json.JSONDecodeError:
            original_valid = False
        
        if original_valid:
            # JSON is already valid, no repair needed
            return RepairTestResult(
                success=True,
                original=broken_json,
                repaired=broken_json,
                valid_json=True,
                error="Input JSON was already valid"
            )
        
        # Use StreamFix FSM to repair the JSON
        preproc_state = PreprocessState()
        fsm_state = JsonFsmState()
        
        # Process the broken JSON through FSM
        for chunk in [broken_json]:  # Single chunk for testing
            extracted = preprocess_chunk(chunk, preproc_state)
            if extracted:
                fsm_feed(fsm_state, extracted)
        
        # Finalize preprocessing and FSM
        final_extracted = preprocess_finalize(preproc_state)
        if final_extracted:
            fsm_feed(fsm_state, final_extracted)
        
        fsm_finalize(fsm_state)
        extracted_json, fsm_status = fsm_result(fsm_state)
        
        # Apply repair to extracted JSON
        if fsm_status in ["DONE", "TRUNCATED"] and extracted_json.strip():
            repaired_json = safe_repair(extracted_json, fsm_state)
        else:
            # Fallback to direct repair on original text
            repaired_json = safe_repair(broken_json)
        
        # Test if repaired JSON is valid
        valid_json = True
        error = None
        try:
            json.loads(repaired_json)
        except json.JSONDecodeError as e:
            valid_json = False
            error = f"Repair failed: {str(e)}"
        
        return RepairTestResult(
            success=valid_json,
            original=broken_json,
            repaired=repaired_json,
            valid_json=valid_json,
            error=error
        )
        
    except Exception as e:
        return RepairTestResult(
            success=False,
            original=request.broken_json,
            repaired="",
            valid_json=False,
            error=f"Processing error: {str(e)}"
        )