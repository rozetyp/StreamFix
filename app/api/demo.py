"""
Demo endpoint showing OpenRouter + FSM integration
"""
import json
from typing import Dict, Any
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.core.stream_processor import JSONStreamProcessor

router = APIRouter()


@router.post("/v1/demo/fsm")
async def demo_fsm_processing(request: Request) -> Dict[str, Any]:
    """
    Demo endpoint showing FSM JSON processing
    """
    body = await request.json()
    test_content = body.get("content", "Here's some broken JSON: {\"key\": \"value\"")
    
    # Test FSM processing
    processor = JSONStreamProcessor()
    processed = processor.process_complete(test_content)
    
    return {
        "original": test_content,
        "processed": processed,
        "fsm_applied": processed != test_content
    }


@router.post("/v1/demo/stream")
async def demo_streaming(request: Request):
    """
    Demo streaming endpoint with mock SSE data
    """
    body = await request.json()
    
    # Mock streaming response
    async def mock_stream():
        # Simulate OpenAI-style streaming chunks
        chunks = [
            {"choices": [{"delta": {"content": "Hello"}}]},
            {"choices": [{"delta": {"content": " there!"}}]},
            {"choices": [{"delta": {"content": " Here's some JSON: {\"test\": true"}}]},
            {"choices": [{"delta": {"content": ", \"broken\": \"value\""}}]},
            {"choices": [{"delta": {"content": "}"}}]},
        ]
        
        for chunk in chunks:
            yield f"data: {json.dumps(chunk)}\\n\\n"
        
        yield "data: [DONE]\\n\\n"
    
    return StreamingResponse(
        mock_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )