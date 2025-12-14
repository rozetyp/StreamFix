#!/usr/bin/env python3
"""
Test Contract Mode Schema Validation
"""
import json
import requests

# Test schema for API responses
API_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["success", "error"]},
        "data": {"type": "object"},
        "message": {"type": "string"}
    },
    "required": ["status"]
}

# Test data that will need repair
BROKEN_JSON_WITH_SCHEMA = '''
{
  "model": "openai/gpt-4o-mini",
  "messages": [{"role": "user", "content": "Return exactly: {\\"name\\": \\"test\\", \\"age\\": 25, \\"valid\\": true}"}],
  "temperature": 0.1,
  "stream": false,
  "schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "age": {"type": "integer", "minimum": 0},
      "valid": {"type": "boolean"}
    },
    "required": ["name", "age", "valid"]
  }
}
'''

def test_contract_mode():
    print("🧪 Testing Contract Mode Schema Validation")
    
    # Test 1: Request with schema validation
    print("\n📋 Test 1: API request with schema validation")
    
    try:
        response = requests.post(
            "http://127.0.0.1:8002/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            data=BROKEN_JSON_WITH_SCHEMA,
            stream=False
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check if response includes repair artifacts
            if 'choices' in data and len(data['choices']) > 0:
                print("\n✅ Response received successfully")
                content = data['choices'][0].get('message', {}).get('content', '')
                print(f"Content: {content}")
                
                # Check if content can be parsed as JSON
                try:
                    parsed_content = json.loads(content)
                    print(f"✅ Content is valid JSON: {parsed_content}")
                    
                    # Validate against our test schema
                    if all(key in parsed_content for key in ['name', 'age', 'valid']):
                        print("✅ Content matches expected schema structure")
                    else:
                        print("❌ Content doesn't match expected schema")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Content is not valid JSON: {e}")
            else:
                print("❌ No choices in response")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

    # Test 2: Check repair artifacts endpoint
    print("\n📊 Test 2: Check repair artifacts endpoint")
    
    try:
        response = requests.get("http://127.0.0.1:8002/artifacts")
        
        if response.status_code == 200:
            artifacts = response.json()
            print(f"✅ Retrieved {len(artifacts)} artifacts")
            
            # Look for artifacts with schema validation results
            schema_artifacts = [a for a in artifacts if 'schema_validation' in a]
            print(f"📝 Found {len(schema_artifacts)} artifacts with schema validation")
            
            if schema_artifacts:
                latest = schema_artifacts[-1]
                print(f"\n🔍 Latest schema artifact:")
                print(json.dumps(latest, indent=2))
            else:
                print("ℹ️  No schema validation artifacts yet")
                
        else:
            print(f"❌ Artifacts request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Artifacts request failed: {e}")

    print("\n✨ Contract Mode test complete!")

if __name__ == "__main__":
    test_contract_mode()