"""
OpenRouter proxy endpoint with FSM streaming support
"""
import json
import os
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import httpx
from app.core.stream_processor import create_fsm_stream

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    OpenAI-compatible chat completions endpoint
    Proxies to OpenRouter with FSM-based JSON repair
    """
    body = await request.json()
    
    # Use a default OpenRouter key for testing
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY environment variable not set")
    
    # Get upstream base URL from environment (for testing with mock)
    upstream_base_url = os.getenv("UPSTREAM_BASE_URL", "https://openrouter.ai/api/v1")
    upstream_url = f"{upstream_base_url}/chat/completions"
    
    # Set default model if none provided
    if "model" not in body or not body["model"]:
        body["model"] = "anthropic/claude-3.5-sonnet"
    
    # Determine if streaming
    stream = body.get("stream", False)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if stream:
                # Streaming response with FSM processing
                response = await client.post(
                    upstream_url,
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:8000",
                        "X-Title": "StreamFix Gateway",
                    },
                    json=body,
                    timeout=None
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"OpenRouter error: {response.text}"
                    )
                
                # Use FSM stream processor
                fsm_stream = await create_fsm_stream(response)
                
                return StreamingResponse(
                    fsm_stream,
                    media_type="text/event-stream",  # Proper SSE media type
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive"
                    }
                )
            else:
                # Non-streaming response
                response = await client.post(
                    upstream_url,
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:8000", 
                        "X-Title": "StreamFix Gateway",
                    },
                    json=body
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"OpenRouter error: {response.text}"
                    )
                
                return response.json()
                
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Request failed: {str(e)}"
        )