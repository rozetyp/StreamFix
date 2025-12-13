"""
Simple chat completions API endpoint - OpenAI compatible
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.core.auth import get_current_project
from app.models.database import Project, ApiKey
from app.db import get_db

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    current: tuple = Depends(get_current_project),  # (Project, ApiKey)
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    OpenAI-compatible chat completions endpoint
    Returns a simple success response for testing
    """
    project, api_key = current
    body = await request.json()
    
    # Simple success response for testing
    return {
        "id": "chatcmpl-test", 
        "object": "chat.completion",
        "created": 1677652288,
        "model": body.get("model", "test-model"),
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! This is a test response from StreamFix Gateway - authentication working!"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }