#!/usr/bin/env python3
"""
Basic StreamFix integration with OpenAI Python SDK
Demonstrates JSON repair and schema validation
"""

from openai import OpenAI
import json

def main():
    # Create OpenAI client pointing to StreamFix
    # Make sure StreamFix is running: streamfix serve
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="your-openai-key"  # Replace with your actual key
    )
    
    print("🔧 StreamFix + OpenAI Example")
    print("=" * 50)
    
    # Example 1: Basic JSON repair
    print("\n1. Basic JSON Repair (Phase 1)")
    print("-" * 30)
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "Return broken JSON: {name: Alice, age: 25,}"}
        ],
        temperature=0.1
    )
    
    content = response.choices[0].message.content
    print(f"Raw response: {content}")
    
    # StreamFix should have repaired it automatically
    try:
        parsed = json.loads(content)
        print(f"✅ Parsed successfully: {parsed}")
    except json.JSONDecodeError:
        print("❌ Still broken JSON")
    
    # Example 2: Schema validation (Contract Mode)
    print("\n2. Contract Mode Schema Validation (Phase 2)")
    print("-" * 50)
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "Extract person data: John Doe is 30 years old"}
        ],
        # Adding schema triggers Contract Mode
        schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            },
            "required": ["name", "age"]
        },
        temperature=0.1
    )
    
    content = response.choices[0].message.content
    request_id = response.headers.get("x-streamfix-request-id")
    
    print(f"Response: {content}")
    print(f"Request ID: {request_id}")
    
    # Get validation details from StreamFix
    if request_id:
        import requests
        artifact = requests.get(f"http://localhost:8000/result/{request_id}").json()
        
        print(f"\nSchema validation details:")
        print(f"  Extracted JSON: {artifact.get('extracted_json')}")
        print(f"  Schema valid: {artifact.get('schema_valid')}")
        print(f"  Extraction status: {artifact.get('extraction_status')}")
        
        if not artifact.get('schema_valid'):
            print(f"  Validation errors: {artifact.get('schema_errors')}")
    
    print("\n✅ StreamFix integration working!")
    print("\nNext steps:")
    print("- Replace 'your-openai-key' with real API key")
    print("- Try different models and schemas")
    print("- Check out Contract Mode features")

if __name__ == "__main__":
    main()