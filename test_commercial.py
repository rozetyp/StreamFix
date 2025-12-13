#!/usr/bin/env python3
"""
Commercial StreamFix Validation
Test the actual commercial use case with real performance data
"""
import asyncio
import httpx
import json
import time
from typing import List, Dict

# Your OpenAI API key
OPENAI_KEY = "your-openai-key-here"

STREAMFIX_URL = "https://streamfix.up.railway.app"
OPENAI_URL = "https://api.openai.com"

async def test_commercial_streaming():
    """Test the actual commercial scenario: developer replaces OpenAI URL with StreamFix"""
    
    print("🏢 COMMERCIAL STREAMFIX VALIDATION")
    print("="*60)
    print("Testing the main use case: transparent JSON repair in streaming")
    print()
    
    # Real commercial request that would break with malformed JSON
    request_data = {
        "model": "gpt-3.5-turbo",
        "stream": True,
        "temperature": 0.7,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Always respond with valid JSON objects, but you sometimes make syntax errors like trailing commas."
            },
            {
                "role": "user", 
                "content": "Return a JSON response with these fields: status, result, metadata. Make it realistic but include a trailing comma error."
            }
        ]
    }
    
    print("📋 Test Scenario:")
    print("   • Client makes normal OpenAI streaming request")
    print("   • LLM returns JSON with syntax errors (trailing commas, etc)")  
    print("   • StreamFix transparently repairs the JSON")
    print("   • Client receives clean, parseable response")
    print()
    
    # Test 1: Direct OpenAI (baseline)
    print("🧪 Test 1: Direct OpenAI (baseline)")
    print("-" * 40)
    
    direct_start = time.time()
    direct_chunks = []
    direct_events = 0
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                f"{OPENAI_URL}/v1/chat/completions",
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_KEY}"
                }
            ) as response:
                
                if response.status_code != 200:
                    print(f"❌ OpenAI error: {response.status_code}")
                    return False
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        direct_events += 1
                        data = line[6:]
                        
                        if data.strip() == "[DONE]":
                            break
                            
                        try:
                            event = json.loads(data)
                            if "choices" in event and len(event["choices"]) > 0:
                                delta = event["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    direct_chunks.append(content)
                        except json.JSONDecodeError:
                            print(f"⚠️  Malformed event: {data[:50]}...")
        
        direct_duration = time.time() - direct_start
        direct_content = "".join(direct_chunks)
        
        print(f"✅ Direct OpenAI completed in {direct_duration:.2f}s")
        print(f"   Events: {direct_events}, Content chunks: {len(direct_chunks)}")
        print(f"   Content: {direct_content[:100]}...")
        
        # Test if content is valid JSON
        try:
            json.loads(direct_content)
            direct_valid = True
            print("   ✅ Content is valid JSON")
        except json.JSONDecodeError as e:
            direct_valid = False
            print(f"   ❌ Content is invalid JSON: {e}")
            
    except Exception as e:
        print(f"❌ Direct test failed: {e}")
        return False
    
    print()
    
    # Test 2: StreamFix Proxy (commercial scenario)
    print("🧪 Test 2: StreamFix Proxy (commercial use case)")
    print("-" * 50)
    
    streamfix_start = time.time()
    streamfix_chunks = []
    streamfix_events = 0
    request_id = None
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                f"{STREAMFIX_URL}/v1/chat/completions",
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_KEY}",
                    "X-StreamFix-Target": f"{OPENAI_URL}/v1/chat/completions"
                }
            ) as response:
                
                if response.status_code != 200:
                    print(f"❌ StreamFix error: {response.status_code}")
                    return False
                
                # Check StreamFix headers
                request_id = response.headers.get("X-StreamFix-Request-Id")
                if request_id:
                    print(f"🔍 StreamFix Request ID: {request_id}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        streamfix_events += 1
                        data = line[6:]
                        
                        if data.strip() == "[DONE]":
                            break
                            
                        try:
                            event = json.loads(data)
                            if "choices" in event and len(event["choices"]) > 0:
                                delta = event["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    streamfix_chunks.append(content)
                        except json.JSONDecodeError:
                            print(f"⚠️  Malformed event: {data[:50]}...")
        
        streamfix_duration = time.time() - streamfix_start
        streamfix_content = "".join(streamfix_chunks)
        
        print(f"✅ StreamFix completed in {streamfix_duration:.2f}s")
        print(f"   Events: {streamfix_events}, Content chunks: {len(streamfix_chunks)}")
        print(f"   Content: {streamfix_content[:100]}...")
        
        # Test if content is valid JSON
        try:
            json.loads(streamfix_content)
            streamfix_valid = True
            print("   ✅ Content is valid JSON")
        except json.JSONDecodeError as e:
            streamfix_valid = False
            print(f"   ❌ Content is invalid JSON: {e}")
            
    except Exception as e:
        print(f"❌ StreamFix test failed: {e}")
        return False
    
    print()
    
    # Get repair details
    if request_id:
        print("🔧 StreamFix Repair Analysis")
        print("-" * 30)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                repair_resp = await client.get(f"{STREAMFIX_URL}/result/{request_id}")
                
                if repair_resp.status_code == 200:
                    repair_data = repair_resp.json()
                    print(f"   Status: {repair_data.get('status', 'unknown')}")
                    print(f"   Parse OK: {repair_data.get('parse_ok', 'unknown')}")
                    
                    original = repair_data.get('original_json', '')
                    repaired = repair_data.get('repaired_json', '')
                    
                    if original != repaired:
                        print(f"   🔧 JSON was repaired!")
                        print(f"   Original: {original[:50]}...")
                        print(f"   Repaired: {repaired[:50]}...")
                    else:
                        print(f"   ✅ No repair needed")
                        
        except Exception as e:
            print(f"   ⚠️  Could not get repair details: {e}")
    
    print()
    print("📊 PERFORMANCE ANALYSIS")
    print("=" * 30)
    print(f"Direct OpenAI:   {direct_duration:.3f}s")
    print(f"StreamFix Proxy: {streamfix_duration:.3f}s")
    
    overhead = streamfix_duration - direct_duration
    overhead_pct = (overhead / direct_duration) * 100
    
    print(f"Overhead:        {overhead:.3f}s ({overhead_pct:+.1f}%)")
    
    if overhead_pct < 10:
        print("✅ Excellent performance - minimal overhead")
    elif overhead_pct < 25:
        print("✅ Good performance - acceptable overhead")
    else:
        print("⚠️  High overhead - may need optimization")
    
    print()
    print("🎯 COMMERCIAL VALIDATION RESULT")
    print("=" * 40)
    
    if streamfix_valid and not direct_valid:
        print("🎉 SUCCESS: StreamFix fixed invalid JSON from OpenAI!")
        print("   • Direct OpenAI: Invalid JSON")
        print("   • StreamFix Proxy: Valid JSON ✅")
        print("   • Commercial value demonstrated!")
        
    elif streamfix_valid and direct_valid:
        print("✅ SUCCESS: Both responses valid, StreamFix transparent")
        print("   • Direct OpenAI: Valid JSON ✅")
        print("   • StreamFix Proxy: Valid JSON ✅")
        print("   • No repair needed, but system works correctly")
        
    elif not streamfix_valid:
        print("❌ FAILURE: StreamFix did not fix the JSON")
        print("   • This needs investigation")
        
    return streamfix_valid

async def test_latency_benchmark():
    """Quick latency benchmark"""
    
    print("\n🚀 LATENCY BENCHMARK")
    print("=" * 30)
    print("Testing response time for simple requests...")
    
    simple_request = {
        "model": "gpt-3.5-turbo",
        "stream": False,  # Non-streaming for latency test
        "messages": [{"role": "user", "content": "Hello"}]
    }
    
    # Test multiple requests
    streamfix_times = []
    
    for i in range(3):
        start = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{STREAMFIX_URL}/v1/chat/completions",
                    json=simple_request,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {OPENAI_KEY}",
                        "X-StreamFix-Target": f"{OPENAI_URL}/v1/chat/completions"
                    }
                )
                
                if response.status_code == 200:
                    duration = time.time() - start
                    streamfix_times.append(duration)
                    print(f"   Request {i+1}: {duration:.3f}s")
                else:
                    print(f"   Request {i+1}: FAILED")
                    
        except Exception as e:
            print(f"   Request {i+1}: ERROR - {e}")
    
    if streamfix_times:
        avg_time = sum(streamfix_times) / len(streamfix_times)
        print(f"\nAverage response time: {avg_time:.3f}s")
        
        if avg_time < 1.0:
            print("✅ Excellent latency")
        elif avg_time < 2.0:
            print("✅ Good latency")
        else:
            print("⚠️  High latency")

if __name__ == "__main__":
    async def main():
        success = await test_commercial_streaming()
        await test_latency_benchmark()
        
        print(f"\n🏢 COMMERCIAL READINESS: {'✅ READY' if success else '❌ NOT READY'}")
        
        print(f"\n💡 ABOUT THE /test ENDPOINT:")
        print(f"   • Development/debugging tool")
        print(f"   • Allows testing repair logic without API costs")
        print(f"   • Not needed for production customers")
        print(f"   • Main product is transparent streaming proxy")
        
    asyncio.run(main())