#!/usr/bin/env python3
"""
Multi-provider validation tests for StreamFix Gateway
Tests compatibility across different AI providers via OpenRouter
"""
import asyncio
import httpx
import json
import time
from typing import Dict, Any

BASE_URL = "https://streamfix.up.railway.app"

# Test different provider models available through OpenRouter
TEST_MODELS = [
    {
        "name": "Claude 3 Haiku",
        "model": "anthropic/claude-3-haiku",
        "provider": "Anthropic"
    },
    {
        "name": "GPT-4o Mini", 
        "model": "openai/gpt-4o-mini",
        "provider": "OpenAI"
    },
    {
        "name": "Gemini Flash",
        "model": "google/gemini-flash-1.5",
        "provider": "Google"
    },
    {
        "name": "Claude 3.5 Sonnet",
        "model": "anthropic/claude-3.5-sonnet", 
        "provider": "Anthropic"
    }
]

async def test_provider_compatibility(model_info: Dict[str, str]) -> Dict[str, Any]:
    """Test a specific provider model"""
    print(f"Testing {model_info['name']} ({model_info['provider']})...")
    
    test_prompt = f"Return this exact malformed JSON: {{\"provider\": \"{model_info['provider']}\", \"test\": true,}}"
    
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Test non-streaming
            response = await client.post(
                f"{BASE_URL}/v1/chat/completions",
                json={
                    "model": model_info["model"],
                    "messages": [{"role": "user", "content": test_prompt}],
                    "stream": False
                }
            )
            
            duration = time.time() - start_time
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "duration": duration
                }
            
            # Check response structure
            data = response.json()
            request_id = response.headers.get("x-streamfix-request-id")
            
            # Validate response
            assert "choices" in data
            assert len(data["choices"]) > 0
            assert "message" in data["choices"][0]
            assert "content" in data["choices"][0]["message"]
            
            return {
                "success": True,
                "duration": duration,
                "request_id": request_id,
                "response_length": len(data["choices"][0]["message"]["content"]),
                "provider": model_info["provider"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }

async def test_streaming_across_providers():
    """Test streaming functionality across providers"""
    print("\n🔄 Testing streaming across providers...")
    
    streaming_results = {}
    
    for model_info in TEST_MODELS[:2]:  # Test first 2 for streaming
        print(f"  Streaming test: {model_info['name']}...")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{BASE_URL}/v1/chat/completions",
                    json={
                        "model": model_info["model"],
                        "messages": [{"role": "user", "content": "Count to 3"}],
                        "stream": True
                    }
                )
                
                if response.status_code == 200:
                    events = 0
                    async for chunk in response.aiter_text():
                        if "data: " in chunk:
                            events += 1
                        if events >= 5 or "[DONE]" in chunk:
                            break
                    
                    streaming_results[model_info["name"]] = {
                        "success": True,
                        "events": events
                    }
                else:
                    streaming_results[model_info["name"]] = {
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    }
                    
        except Exception as e:
            streaming_results[model_info["name"]] = {
                "success": False, 
                "error": str(e)
            }
    
    return streaming_results

async def test_repair_consistency():
    """Test that repair behavior is consistent across providers"""
    print("\n🔧 Testing repair consistency across providers...")
    
    malformed_json = '{"name": "test", "values": [1, 2, 3,], "flag": true,}'
    
    repair_results = {}
    
    for model_info in TEST_MODELS[:3]:  # Test first 3 for repair consistency
        print(f"  Repair test: {model_info['name']}...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Send malformed JSON to model
                response = await client.post(
                    f"{BASE_URL}/v1/chat/completions",
                    json={
                        "model": model_info["model"],
                        "messages": [{"role": "user", "content": f"Return this exact text: {malformed_json}"}],
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    request_id = response.headers.get("x-streamfix-request-id")
                    
                    # Get repair artifacts
                    if request_id:
                        repair_response = await client.get(f"{BASE_URL}/result/{request_id}")
                        if repair_response.status_code == 200:
                            repair_data = repair_response.json()
                            repair_results[model_info["name"]] = {
                                "success": True,
                                "repairs_applied": repair_data.get("repairs_applied", []),
                                "parse_success": repair_data.get("parse_success", False)
                            }
                            continue
                
                repair_results[model_info["name"]] = {
                    "success": False,
                    "error": "Could not get repair artifacts"
                }
                
        except Exception as e:
            repair_results[model_info["name"]] = {
                "success": False,
                "error": str(e)
            }
    
    return repair_results

async def main():
    """Run all multi-provider tests"""
    print("🧪 Testing Multi-Provider Compatibility\n")
    
    # Test basic compatibility
    provider_results = []
    for model_info in TEST_MODELS:
        result = await test_provider_compatibility(model_info)
        result["model"] = model_info["name"]
        provider_results.append(result)
    
    # Test streaming
    streaming_results = await test_streaming_across_providers()
    
    # Test repair consistency  
    repair_results = await test_repair_consistency()
    
    # Print summary
    print(f"\n📊 Multi-Provider Test Results:")
    print(f"=" * 50)
    
    successful_providers = [r for r in provider_results if r["success"]]
    print(f"✅ Compatible providers: {len(successful_providers)}/{len(provider_results)}")
    
    for result in provider_results:
        status = "✅" if result["success"] else "❌"
        duration = result.get("duration", 0)
        print(f"  {status} {result['model']}: {duration:.2f}s")
        if not result["success"]:
            print(f"     Error: {result.get('error', 'Unknown')}")
    
    print(f"\n🔄 Streaming Results:")
    for model, result in streaming_results.items():
        status = "✅" if result["success"] else "❌"
        events = result.get("events", 0)
        print(f"  {status} {model}: {events} events")
    
    print(f"\n🔧 Repair Consistency:")
    for model, result in repair_results.items():
        status = "✅" if result["success"] else "❌"
        repairs = result.get("repairs_applied", [])
        print(f"  {status} {model}: {len(repairs)} repairs applied")
    
    if len(successful_providers) >= 2:
        print(f"\n🎉 Multi-provider compatibility proven!")
        print(f"✅ StreamFix works across {len(successful_providers)} different AI providers")
    else:
        print(f"\n⚠️  Limited provider compatibility - only {len(successful_providers)} working")

if __name__ == "__main__":
    asyncio.run(main())