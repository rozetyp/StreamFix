#!/usr/bin/env python3
"""
Real end-to-end streaming test with actual LLM
Tests the complete SSE pipeline through StreamFix
"""
import asyncio
import httpx
import json
import time
from typing import AsyncGenerator

# Test against production StreamFix
STREAMFIX_URL = "https://streamfix.up.railway.app"

async def test_real_streaming():
    """Test actual streaming through StreamFix to a real LLM"""
    
    # Use OpenAI as real upstream (requires API key)
    api_key = input("Enter OpenAI API key for real streaming test (or 'skip'): ").strip()
    if api_key.lower() == 'skip':
        print("⏭️  Skipping real streaming test (no API key)")
        return False
    
    print("🧪 Testing Real Streaming Pipeline")
    print("=" * 50)
    
    # Request that should produce broken JSON
    request_data = {
        "model": "gpt-3.5-turbo",
        "stream": True,
        "messages": [
            {
                "role": "user", 
                "content": "Return this exact broken JSON with trailing comma: {\"result\": \"success\", \"count\": 5,}"
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-StreamFix-Target": "https://api.openai.com/v1/chat/completions",
        "Authorization": f"Bearer {api_key}"
    }
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                f"{STREAMFIX_URL}/v1/chat/completions",
                json=request_data,
                headers=headers
            ) as response:
                
                if response.status_code != 200:
                    print(f"❌ HTTP {response.status_code}: {response.text}")
                    return False
                
                print(f"✅ Streaming started (HTTP {response.status_code})")
                
                # Check for StreamFix headers
                request_id = response.headers.get("X-StreamFix-Request-Id")
                if request_id:
                    print(f"🔍 StreamFix Request ID: {request_id}")
                else:
                    print("⚠️  No StreamFix Request ID header")
                
                # Read SSE stream
                content_chunks = []
                event_count = 0
                
                async for chunk in response.aiter_lines():
                    if chunk.startswith("data: "):
                        event_count += 1
                        data = chunk[6:]  # Remove "data: " prefix
                        
                        if data.strip() == "[DONE]":
                            print(f"✅ Stream completed with [DONE] after {event_count} events")
                            break
                        
                        try:
                            event_json = json.loads(data)
                            if "choices" in event_json and len(event_json["choices"]) > 0:
                                delta = event_json["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    content_chunks.append(content)
                                    print(f"📦 Chunk {len(content_chunks)}: '{content}'")
                        except json.JSONDecodeError:
                            print(f"⚠️  Invalid JSON in stream: {data}")
                
                # Analyze complete content
                full_content = "".join(content_chunks)
                duration = time.time() - start_time
                
                print("\n" + "=" * 50)
                print("📊 Stream Analysis:")
                print(f"   Duration: {duration:.2f}s")
                print(f"   Events: {event_count}")
                print(f"   Content chunks: {len(content_chunks)}")
                print(f"   Full content: {full_content}")
                
                # Test if StreamFix captured repair info
                if request_id:
                    print("\n🔍 Checking repair results...")
                    repair_response = await client.get(f"{STREAMFIX_URL}/result/{request_id}")
                    
                    if repair_response.status_code == 200:
                        repair_data = repair_response.json()
                        print(f"📋 Repair Status: {repair_data.get('status', 'unknown')}")
                        print(f"🔧 Original JSON: {repair_data.get('original_json', 'N/A')}")
                        print(f"✨ Repaired JSON: {repair_data.get('repaired_json', 'N/A')}")
                        print(f"✅ Parse OK: {repair_data.get('parse_ok', False)}")
                    else:
                        print(f"❌ Could not retrieve repair results: HTTP {repair_response.status_code}")
                
                return True
                
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False

async def test_mock_streaming():
    """Test streaming with our mock server"""
    
    print("🧪 Testing Mock Streaming (No API Key Required)")
    print("=" * 50)
    
    # First, check if we have a mock server available
    # For now, just test our streaming response format
    
    mock_request = {
        "model": "mock-model",
        "stream": True,
        "messages": [
            {"role": "user", "content": "Return broken JSON"}
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{STREAMFIX_URL}/v1/demo/stream", 
                json=mock_request
            )
            
            print(f"Mock demo response: {response.status_code}")
            if response.status_code == 200:
                print("✅ Demo streaming endpoint is working")
                return True
            else:
                print(f"❌ Demo endpoint failed: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Mock streaming test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 StreamFix End-to-End Streaming Test")
    print("Testing the complete SSE pipeline with real/mock LLMs")
    print()
    
    async def main():
        # Test 1: Real streaming (optional)
        real_success = await test_real_streaming()
        
        print("\n")
        
        # Test 2: Mock streaming (always)
        mock_success = await test_mock_streaming()
        
        print("\n" + "=" * 50)
        print("🎯 STREAMING TEST SUMMARY")
        print(f"Real LLM Streaming: {'✅ PASS' if real_success else '❌ FAIL/SKIP'}")
        print(f"Mock Streaming: {'✅ PASS' if mock_success else '❌ FAIL'}")
        
        if mock_success:
            print("\n🎉 StreamFix streaming pipeline is working!")
        else:
            print("\n❌ StreamFix streaming has issues")
    
    asyncio.run(main())