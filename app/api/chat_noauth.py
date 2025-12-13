"""
OpenRouter proxy endpoint with FSM streaming support
"""
import json
import os
import uuid
import datetime
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import StreamingResponse
import httpx
from app.core.stream_processor import create_fsm_stream
from app.core.repair import safe_repair

# Simple in-memory store for repair artifacts (last 100 requests)
repair_artifacts = {}
MAX_ARTIFACTS = 100

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(request: Request, response: Response):
    """
    OpenAI-compatible chat completions endpoint
    Proxies to OpenRouter with FSM-based JSON repair
    """
    body = await request.json()
    
    # Generate request ID for tracking
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    response.headers["x-streamfix-request-id"] = request_id
    
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
                
                # Get response content and attempt repair
                response_data = response.json()
                original_content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                model = body.get("model", "unknown")
                
                # Store repair artifact
                repair_info = store_repair_artifact(request_id, original_content, model)
                
                # Return potentially repaired response
                if repair_info["repaired_content"] != original_content:
                    response_data["choices"][0]["message"]["content"] = repair_info["repaired_content"]
                
                return response_data
                
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Request failed: {str(e)}"
        )


def store_repair_artifact(request_id: str, content: str, model: str) -> dict:
    """Store repair artifact and return repair info"""
    global repair_artifacts
    
    # Attempt repair
    try:
        repaired_content = safe_repair(content) if content else content
        repairs_applied = []
        parse_success = True
        
        # Simple repair detection
        if content != repaired_content:
            if ',' in content and ',' not in repaired_content.replace(',', ''):
                repairs_applied.append("remove_trailing_comma")
            if '{' in content and '"' not in content.split(':')[0]:
                repairs_applied.append("quote_unquoted_keys")
        
        # Test if repaired content is valid JSON
        try:
            if repaired_content.strip():
                json.loads(repaired_content)
        except json.JSONDecodeError:
            parse_success = False
            
    except Exception:
        repaired_content = content
        repairs_applied = []
        parse_success = False
    
    # Store artifact
    artifact = {
        "request_id": request_id,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "model": model,
        "original_content": content,
        "repaired_content": repaired_content,
        "repairs_applied": repairs_applied,
        "parse_success": parse_success,
        "status": "REPAIRED" if repairs_applied else "PASSTHROUGH"
    }
    
    # Keep only last MAX_ARTIFACTS
    if len(repair_artifacts) >= MAX_ARTIFACTS:
        oldest_key = min(repair_artifacts.keys(), key=lambda k: repair_artifacts[k]["timestamp"])
        del repair_artifacts[oldest_key]
    
    repair_artifacts[request_id] = artifact
    return artifact


@router.get("/result/{request_id}")
async def get_repair_result(request_id: str):
    """Get repair artifact for a specific request"""
    if request_id not in repair_artifacts:
        raise HTTPException(status_code=404, detail="Request ID not found")
    
    return repair_artifacts[request_id]


@router.get("/metrics")
async def get_metrics():
    """Get basic repair metrics"""
    if not repair_artifacts:
        return {"message": "No repair data available"}
    
    total = len(repair_artifacts)
    repaired = sum(1 for a in repair_artifacts.values() if a["status"] == "REPAIRED")
    parse_success = sum(1 for a in repair_artifacts.values() if a["parse_success"])
    
    # Count repair types
    repair_types = {}
    for artifact in repair_artifacts.values():
        for repair_type in artifact["repairs_applied"]:
            repair_types[repair_type] = repair_types.get(repair_type, 0) + 1
    
    return {
        "total_requests": total,
        "repair_rate": round(repaired / total, 3) if total > 0 else 0,
        "parse_success_rate": round(parse_success / total, 3) if total > 0 else 0,
        "repair_types": repair_types,
        "last_updated": datetime.datetime.utcnow().isoformat()
    }