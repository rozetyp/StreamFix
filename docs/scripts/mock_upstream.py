#!/usr/bin/env python3
"""
Mock OpenRouter-compatible upstream server for deterministic testing.
Provides controlled responses with proper SSE format and JSON repair scenarios.
"""
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
import time

app = FastAPI(title="Mock Upstream", description="OpenRouter-compatible test server")

@app.post("/chat/completions")
@app.post("/v1/chat/completions") 
async def chat(request: Request):
    """Mock upstream that streams OpenRouter-compatible SSE with JSON content"""
    
    # Get request body
    try:
        body = await request.json()
        stream = body.get("stream", False)
        model = body.get("model", "mock-model")
        messages = body.get("messages", [])
    except:
        stream = False
        model = "mock-model"
        messages = []
    
    if not stream:
        # Non-streaming response - return structured JSON like OpenAI/OpenRouter
        return {
            "id": "chatcmpl-mock",
            "object": "chat.completion", 
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": 'Here\'s the JSON you requested:\n\n```json\n{\n  "status": "success",\n  "data": [1, 2, 3],\n  "items": [\n    {"name": "item1", "value": 10,},\n    {"name": "item2", "value": 20,}\n  ],\n  "total": 30,\n}\n```\n\nThat JSON has trailing commas that need repair.'
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 50,
                "total_tokens": 60
            }
        }
    
    # Streaming response with proper OpenRouter SSE format
    async def generate_sse_chunks():
        """Generate properly formatted SSE chunks like OpenRouter"""
        request_id = f"chatcmpl-mock-{int(time.time())}"
        
        # Determine content based on user request
        content = ""
        if messages:
            user_content = messages[-1].get("content", "").lower()
            if "trailing" in user_content and "comma" in user_content:
                # Specific trailing comma scenario
                json_content = '{\n  "test": true,\n  "items": [1,2,3,],\n  "result": "success",\n}'
            else:
                # Default scenario with various JSON issues
                json_content = '{\n  "status": "success",\n  "data": [1, 2, 3],\n  "items": [\n    {"name": "item1", "value": 10,},\n    {"name": "item2", "value": 20,}\n  ],\n  "total": 30,\n}'
        else:
            json_content = '{"simple": "response", "count": 42}'
        
        # Content chunks to stream
        content_parts = [
            "Here's the JSON response:\n\n```json\n",
            json_content,
            "\n```\n\nThat JSON contains trailing commas that need repair."
        ]
        
        # Stream each part as proper SSE chunks
        for i, part in enumerate(content_parts):
            chunk_data = {
                "id": request_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": part},
                    "finish_reason": None
                }]
            }
            
            sse_line = f"data: {json.dumps(chunk_data)}\n\n"
            yield sse_line
            await asyncio.sleep(0.05)  # Faster for testing
        
        # Final chunk with finish_reason
        final_chunk = {
            "id": request_id,
            "object": "chat.completion.chunk", 
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        
        # SSE terminator
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_sse_chunks(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache", 
            "Connection": "keep-alive"
        }
    )

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "mock_upstream", "time": int(time.time())}

if __name__ == "__main__":
    import uvicorn
    print("🧪 Starting Mock Upstream Server...")
    print("   - OpenRouter-compatible SSE format")
    print("   - Trailing comma JSON scenarios")
    print("   - Health check at /health")
    print("   - Running on http://127.0.0.1:1234")
    print()
    uvicorn.run(app, host="127.0.0.1", port=1234, log_level="info")