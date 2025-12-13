"""
Chat completion API endpoint - OpenAI compatible proxy
"""
import time
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.api import ChatCompletionRequest
from app.models.database import Project, ApiKey
from app.core.auth import get_current_project
from app.core.proxy import get_provider_client, log_request_event
from app.db import get_db

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    project_and_key: tuple[Project, ApiKey] = Depends(get_current_project),
    db: Session = Depends(get_db)
):
    """
    OpenAI-compatible chat completions endpoint with StreamFix processing
    """
    project, api_key = project_and_key
    start_time = time.time()
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Get StreamFix metadata
    streamfix_meta = request.streamfix()
    
    # Determine model - use request model or project default
    model = request.model or project.default_model
    if not model:
        raise HTTPException(
            status_code=400, 
            detail="No model specified and no default model configured"
        )
    
    # Get provider client
    try:
        provider = get_provider_client(project, db)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Prepare request body for upstream (remove StreamFix metadata)
    upstream_body = request.model_dump(exclude={"metadata"})
    upstream_body["model"] = model
    
    # Handle streaming vs non-streaming
    stream = request.stream or False
    
    try:
        if stream:
            return await _handle_streaming_request(
                provider, upstream_body, project, api_key, request_id, model, start_time, db
            )
        else:
            return await _handle_non_streaming_request(
                provider, upstream_body, project, api_key, request_id, model, start_time, db
            )
    
    except Exception as e:
        # Log error event
        await log_request_event(
            db=db,
            project_id=str(project.id),
            api_key_id=str(api_key.id),
            request_id=request_id,
            provider=project.default_provider,
            model=model,
            stream=stream,
            status="UPSTREAM_ERROR",
            latency_ms_total=int((time.time() - start_time) * 1000),
            error_detail={"error": str(e)}
        )
        
        # Re-raise as HTTP error
        raise HTTPException(status_code=500, detail="Upstream request failed")
    
    finally:
        await provider.close()


async def _handle_non_streaming_request(
    provider,
    upstream_body: Dict[str, Any], 
    project: Project,
    api_key: ApiKey,
    request_id: str,
    model: str,
    start_time: float,
    db: Session
) -> Dict[str, Any]:
    """Handle non-streaming request"""
    
    # Call upstream
    upstream_start = time.time()
    response = await provider.chat_completion(upstream_body, stream=False)
    upstream_latency = int((time.time() - upstream_start) * 1000)
    total_latency = int((time.time() - start_time) * 1000)
    
    # Extract usage info if available
    usage = response.get("usage", {})
    
    # Log success event
    await log_request_event(
        db=db,
        project_id=str(project.id),
        api_key_id=str(api_key.id),
        request_id=request_id,
        provider=project.default_provider,
        model=model,
        stream=False,
        status="OK",
        latency_ms_total=total_latency,
        latency_ms_upstream=upstream_latency,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens")
    )
    
    return response


async def _handle_streaming_request(
    provider,
    upstream_body: Dict[str, Any],
    project: Project, 
    api_key: ApiKey,
    request_id: str,
    model: str,
    start_time: float,
    db: Session
) -> StreamingResponse:
    """Handle streaming request"""
    
    async def stream_generator():
        upstream_start = time.time()
        bytes_out = 0
        
        try:
            async for chunk in provider.chat_completion(upstream_body, stream=True):
                bytes_out += len(chunk)
                yield chunk
            
            # Log success after streaming completes
            upstream_latency = int((time.time() - upstream_start) * 1000)
            total_latency = int((time.time() - start_time) * 1000)
            
            await log_request_event(
                db=db,
                project_id=str(project.id),
                api_key_id=str(api_key.id),
                request_id=request_id,
                provider=project.default_provider,
                model=model,
                stream=True,
                status="OK",
                latency_ms_total=total_latency,
                latency_ms_upstream=upstream_latency,
                bytes_out=bytes_out
            )
            
        except Exception as e:
            # Log error during streaming
            await log_request_event(
                db=db,
                project_id=str(project.id),
                api_key_id=str(api_key.id),
                request_id=request_id,
                provider=project.default_provider,
                model=model,
                stream=True,
                status="UPSTREAM_ERROR", 
                latency_ms_total=int((time.time() - start_time) * 1000),
                error_detail={"error": str(e)}
            )
            raise
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "X-Request-Id": request_id,
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )