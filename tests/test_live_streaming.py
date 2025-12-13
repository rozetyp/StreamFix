#!/usr/bin/env python3
"""
Live SSE streaming tests for StreamFix Gateway
Tests actual Server-Sent Events protocol implementation
"""
import asyncio
import httpx
import json
import time
from typing import AsyncGenerator

BASE_URL = "https://streamfix.up.railway.app"

class SSEClient:
    """Simple SSE client for testing"""
    
    @staticmethod
    async def parse_sse_stream(response: httpx.Response) -> AsyncGenerator[dict, None]:
        """Parse Server-Sent Events from response stream"""
        async for chunk in response.aiter_text():
            # Split by data: lines
            lines = chunk.split("data: ")
            
            for line in lines[1:]:  # Skip first empty split
                # Clean the line
                data_content = line.split("\n")[0].strip()
                
                if data_content == "[DONE]":
                    return
                
                if data_content and data_content != ": OPENROUTER PROCESSING":
                    try:
                        yield json.loads(data_content)
                    except json.JSONDecodeError:
                        print(f"⚠️  Invalid JSON in SSE: {data_content[:100]}...")

async def test_basic_streaming():
    """Test basic SSE streaming functionality"""
    print("Testing basic SSE streaming...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "anthropic/claude-3-haiku",
                "messages": [{"role": "user", "content": "Count to 3 slowly"}],
                "stream": True
            }
        )
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        
        events = []
        start_time = time.time()
        
        async for event in SSEClient.parse_sse_stream(response):
            events.append(event)
            
            # Validate event structure
            assert "choices" in event
            assert len(event["choices"]) > 0
            assert "delta" in event["choices"][0]
            
            if len(events) >= 10:  # Don't collect infinite events
                break
        
        duration = time.time() - start_time
        
        assert len(events) > 0
        print(f"✅ Basic streaming - {len(events)} events in {duration:.2f}s")

async def test_streaming_with_malformed_json():
    """Test SSE streaming with malformed JSON content"""
    print("Testing streaming with malformed JSON...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/v1/chat/completions", 
            json={
                "model": "anthropic/claude-3-haiku",
                "messages": [{"role": "user", "content": "Return this exact malformed JSON in your response: {\"test\": true,}"}],
                "stream": True
            }
        )
        
        assert response.status_code == 200
        # Note: streaming responses don't include x-streamfix-request-id header
        
        events = []
        content_parts = []
        
        async for event in SSEClient.parse_sse_stream(response):
            events.append(event)
            
            # Collect content deltas
            delta = event.get("choices", [{}])[0].get("delta", {})
            if "content" in delta:
                content_parts.append(delta["content"])
        
        # Verify we got streaming events
        assert len(events) > 0
        full_content = "".join(content_parts)
        
        print(f"✅ Malformed JSON streaming - {len(events)} events")
        print(f"   Content: {full_content[:100]}...")

async def test_streaming_with_think_blocks():
    """Test SSE streaming with <think> blocks"""
    print("Testing streaming with think blocks...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "anthropic/claude-3-haiku", 
                "messages": [{"role": "user", "content": "Use <think> blocks in your response, then return JSON"}],
                "stream": True
            }
        )
        
        assert response.status_code == 200
        
        events = []
        async for event in SSEClient.parse_sse_stream(response):
            events.append(event)
            if len(events) >= 15:  # Reasonable limit
                break
        
        assert len(events) > 0
        print(f"✅ Think blocks streaming - {len(events)} events")

async def test_sse_protocol_compliance():
    """Test SSE protocol compliance"""
    print("Testing SSE protocol compliance...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "anthropic/claude-3-haiku",
                "messages": [{"role": "user", "content": "Say hello"}],
                "stream": True  
            }
        )
        
        # Check SSE headers
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type  # Allow charset suffix
        assert "no-cache" in response.headers.get("cache-control", "")
        
        # Check event format
        raw_data = ""
        async for chunk in response.aiter_text():
            raw_data += chunk
            if len(raw_data) > 1000:  # Sample enough data
                break
        
        # Verify proper SSE format
        assert "data: " in raw_data
        assert "[DONE]" in raw_data or len(raw_data) < 1000  # Completion signal or partial data
        
        print("✅ SSE protocol compliance verified")

async def main():
    """Run all live SSE tests"""
    print("🧪 Testing Live SSE Streaming Protocol\n")
    
    try:
        await test_basic_streaming()
        await test_streaming_with_malformed_json() 
        await test_streaming_with_think_blocks()
        await test_sse_protocol_compliance()
        
        print("\n🎉 All live SSE streaming tests passed!")
        print("✅ Proven: Real SSE protocol implementation works")
        
    except Exception as e:
        print(f"\n❌ SSE test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())