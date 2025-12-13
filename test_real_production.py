#!/usr/bin/env python3
"""
REAL Production Test for StreamFix
Tests actual AI models through production StreamFix deployment
"""
import json
import time
import httpx
import asyncio

STREAMFIX_URL = "https://streamfix.up.railway.app"

async def test_real_ai_with_streamfix():
    """Test real AI model through production StreamFix and verify JSON repair"""
    
    print("🚀 Testing REAL AI through StreamFix Production")
    print(f"Endpoint: {STREAMFIX_URL}")
    print("=" * 60)
    
    # Test case: Ask AI to generate JSON that's likely to be malformed
    test_request = {
        "model": "meta-llama/llama-3.2-1b-instruct:free",  # Free model
        "stream": False,
        "messages": [
            {
                "role": "user", 
                "content": "Return ONLY this JSON object with trailing commas (exactly as shown): {\"name\": \"test\", \"items\": [1, 2, 3,], \"metadata\": {\"version\": 1.0,},}"
            }
        ],
        "temperature": 0.1
    }
    
    print("📤 Sending request to real AI model...")
    print(f"Model: {test_request['model']}")
    print(f"Prompt: {test_request['messages'][0]['content'][:60]}...")
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Send request through StreamFix
            response = await client.post(
                f"{STREAMFIX_URL}/v1/chat/completions",
                json=test_request,
                headers={"Content-Type": "application/json"}
            )
            
        duration = time.time() - start_time
        
        print(f"📥 Response received in {duration:.2f}s")
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.text}")
            return False
        
        # Parse the response
        response_data = response.json()
        
        if "choices" not in response_data or not response_data["choices"]:
            print("❌ Invalid response format")
            print(json.dumps(response_data, indent=2))
            return False
        
        ai_content = response_data["choices"][0]["message"]["content"]
        print(f"\n🤖 AI Response:")
        print(f"Raw content: {ai_content}")
        
        # Try to extract and parse JSON from the AI response
        try:
            # The AI might wrap JSON in markdown or add extra text
            content = ai_content.strip()
            
            # Try to find JSON in the response
            if content.startswith('```'):
                # Extract from code block
                lines = content.split('\n')
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith('```'):
                        if in_json:
                            break
                        in_json = True
                        if 'json' in line:
                            continue
                    elif in_json:
                        json_lines.append(line)
                content = '\n'.join(json_lines)
            
            # Parse the JSON to verify it's valid
            parsed_json = json.loads(content)
            
            print(f"\n✅ SUCCESS: JSON parsed successfully!")
            print(f"Parsed JSON: {json.dumps(parsed_json, indent=2)}")
            
            # Verify it contains expected structure
            if isinstance(parsed_json, dict) and "name" in parsed_json:
                print(f"✅ Contains expected 'name' field: {parsed_json['name']}")
                
                if "items" in parsed_json:
                    print(f"✅ Contains expected 'items' field: {parsed_json['items']}")
                    
                print(f"\n🎉 StreamFix successfully handled real AI response!")
                return True
            else:
                print(f"⚠️  JSON valid but missing expected fields")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Content that failed to parse: {repr(content)}")
            return False
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Request failed after {duration:.2f}s: {str(e)}")
        return False

async def test_streamfix_headers():
    """Test StreamFix specific headers and request ID tracking"""
    
    print("\n" + "=" * 60)
    print("🔍 Testing StreamFix Headers and Request ID")
    print("=" * 60)
    
    test_request = {
        "model": "meta-llama/llama-3.2-1b-instruct:free",
        "stream": False,
        "messages": [{"role": "user", "content": "Say hello"}],
        "temperature": 0.1
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{STREAMFIX_URL}/v1/chat/completions",
                json=test_request,
                headers={"Content-Type": "application/json"}
            )
        
        # Check for StreamFix specific headers
        request_id = response.headers.get("X-StreamFix-Request-Id")
        if request_id:
            print(f"✅ StreamFix Request ID: {request_id}")
            
            # Try to get repair result
            async with httpx.AsyncClient(timeout=10.0) as client:
                repair_result = await client.get(f"{STREAMFIX_URL}/streamfix/result/{request_id}")
                
            if repair_result.status_code == 200:
                repair_data = repair_result.json()
                print(f"✅ Repair result retrieved:")
                print(json.dumps(repair_data, indent=2))
            else:
                print(f"⚠️  Repair result not available: {repair_result.status_code}")
        else:
            print("⚠️  No StreamFix Request ID header found")
        
        print(f"Response headers: {dict(response.headers)}")
        
    except Exception as e:
        print(f"❌ Header test failed: {e}")

async def run_production_validation():
    """Run complete production validation"""
    
    # Test 1: Health check
    try:
        async with httpx.AsyncClient() as client:
            health = await client.get(f"{STREAMFIX_URL}/health")
            if health.status_code == 200:
                health_data = health.json()
                print(f"✅ Health: {health_data}")
            else:
                print(f"❌ Health check failed: {health.status_code}")
                return
    except Exception as e:
        print(f"❌ Cannot reach StreamFix: {e}")
        return
    
    # Test 2: Real AI interaction
    success = await test_real_ai_with_streamfix()
    
    # Test 3: StreamFix headers
    await test_streamfix_headers()
    
    print("\n" + "=" * 60)
    print("📊 PRODUCTION VALIDATION COMPLETE")
    print("=" * 60)
    
    if success:
        print("🎉 StreamFix is working correctly in production!")
        print("✅ Real AI models can be accessed through StreamFix")
        print("✅ JSON responses are properly handled and repaired")
    else:
        print("⚠️  Some issues detected - check logs above")

if __name__ == "__main__":
    print("Starting Real Production Validation...")
    asyncio.run(run_production_validation())