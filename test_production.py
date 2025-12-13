#!/usr/bin/env python3
"""
End-to-end test for StreamFix production deployment
Simulates AI models that return broken JSON and tests repair functionality
"""
import json
import time
import httpx
import asyncio
from typing import List, Dict

# Production StreamFix endpoint
STREAMFIX_URL = "https://streamfix.up.railway.app"

# Test cases simulating real AI model JSON problems
TEST_CASES = [
    {
        "name": "DeepSeek Trailing Commas",
        "broken_json": '{"thinking": "Let me solve this...", "answer": "Hello world",}',
        "expected_fields": ["thinking", "answer"]
    },
    {
        "name": "GPT Incomplete Object",
        "broken_json": '{"response": "Here is the solution", "metadata": {"confidence": 0.95',
        "expected_fields": ["response"]
    },
    {
        "name": "Claude Array Issues", 
        "broken_json": '{"items": [1, 2, 3,], "total": 3}',
        "expected_fields": ["items", "total"]
    },
    {
        "name": "Unescaped Quotes",
        "broken_json": '{"text": "He said "Hello world" to me", "source": "conversation"}',
        "expected_fields": ["text", "source"]
    },
    {
        "name": "Mixed Content with Fence",
        "broken_json": '''```json
{"result": "success", "data": [1,2,3,]}
```''',
        "expected_fields": ["result", "data"]
    }
]

async def test_streamfix_repair(test_case: Dict) -> Dict:
    """Test a single JSON repair case against production StreamFix"""
    
    print(f"\n🧪 Testing: {test_case['name']}")
    print(f"   Input: {test_case['broken_json'][:50]}...")
    
    # Create request that would produce this broken JSON
    request_data = {
        "model": "test-model",
        "stream": False,
        "messages": [
            {
                "role": "user", 
                "content": f"Return this exact JSON (it may be malformed): {test_case['broken_json']}"
            }
        ]
    }
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{STREAMFIX_URL}/v1/chat/completions",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
        duration = time.time() - start_time
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "duration": duration
            }
        
        # Try to parse the response JSON
        try:
            response_json = response.json()
            
            # Check if StreamFix properly repaired and returned valid JSON
            if "choices" in response_json and len(response_json["choices"]) > 0:
                content = response_json["choices"][0].get("message", {}).get("content", "")
                
                # Try to parse the content as JSON to verify repair worked
                try:
                    parsed_content = json.loads(content)
                    
                    # Verify expected fields are present
                    missing_fields = [field for field in test_case["expected_fields"] 
                                    if field not in parsed_content]
                    
                    if missing_fields:
                        return {
                            "success": False,
                            "error": f"Missing expected fields: {missing_fields}",
                            "repaired_json": parsed_content,
                            "duration": duration
                        }
                    
                    print(f"   ✅ SUCCESS: JSON repaired correctly in {duration:.2f}s")
                    print(f"   Output: {json.dumps(parsed_content, indent=2)[:100]}...")
                    
                    return {
                        "success": True,
                        "original": test_case["broken_json"],
                        "repaired": parsed_content,
                        "duration": duration
                    }
                    
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "error": f"Repaired content is not valid JSON: {e}",
                        "raw_content": content,
                        "duration": duration
                    }
            else:
                return {
                    "success": False,
                    "error": "Invalid response format from StreamFix",
                    "response": response_json,
                    "duration": duration
                }
                
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"StreamFix response is not valid JSON: {e}",
                "raw_response": response.text,
                "duration": duration
            }
            
    except Exception as e:
        duration = time.time() - start_time
        return {
            "success": False,
            "error": f"Request failed: {str(e)}",
            "duration": duration
        }

async def run_production_tests():
    """Run all StreamFix tests against production deployment"""
    
    print("🚀 StreamFix Production Test Suite")
    print(f"   Testing endpoint: {STREAMFIX_URL}")
    print("=" * 60)
    
    # First, test health endpoint
    try:
        async with httpx.AsyncClient() as client:
            health = await client.get(f"{STREAMFIX_URL}/health")
            if health.status_code == 200:
                print("✅ Health check passed")
            else:
                print(f"❌ Health check failed: {health.status_code}")
                return
    except Exception as e:
        print(f"❌ Cannot reach StreamFix: {e}")
        return
    
    # Run all test cases
    results = []
    for test_case in TEST_CASES:
        result = await test_streamfix_repair(test_case)
        result["test_name"] = test_case["name"]
        results.append(result)
        
        # Add small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! StreamFix is working correctly in production!")
    else:
        print(f"\n❌ {total-passed} tests failed:")
        for result in results:
            if not result["success"]:
                print(f"   • {result['test_name']}: {result['error']}")
    
    # Performance summary
    avg_duration = sum(r["duration"] for r in results) / len(results)
    print(f"\nPerformance: Average response time {avg_duration:.2f}s")

if __name__ == "__main__":
    print("Starting StreamFix production validation...")
    asyncio.run(run_production_tests())