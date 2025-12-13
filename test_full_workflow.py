#!/usr/bin/env python3
"""
Full StreamFix Workflow Test
=============================

This script simulates the complete workflow of how StreamFix would work
in a real-world scenario without requiring API keys or external services.

It demonstrates:
1. What typical broken JSON from LLMs looks like
2. How StreamFix repairs it
3. The complete user experience
"""

import json
import requests
import time
from typing import List, Dict, Any

# Production StreamFix URL
STREAMFIX_URL = "https://streamfix.up.railway.app"

class LLMSimulator:
    """Simulates various types of broken JSON that LLMs commonly produce"""
    
    COMMON_BROKEN_EXAMPLES = [
        # Trailing commas
        '{"name": "John", "age": 30, "hobbies": ["reading", "coding",],}',
        
        # Missing quotes
        '{name: "John", age: 30, city: "New York"}',
        
        # Mixed quotes
        """{"name": 'John', "details": {"age": 30, 'city': "Boston"}}""",
        
        # Unescaped strings
        '{"message": "He said "Hello world" to everyone", "status": "ok"}',
        
        # Incomplete objects
        '{"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"',
        
        # Multiple JSON objects in text
        'Here is your data: {"result": "success", "count": 5,} and {"error": null,}',
        
        # Complex nested with multiple issues
        """{
            "response": {
                "data": [
                    {"id": 1, "name": "Product A", "price": 29.99,},
                    {"id": 2, name: "Product B", "price": 39.99}
                ],
                "meta": {
                    "total": 2,
                    "page": 1,
                }
            },
        }""",
        
        # LLM explanation with JSON
        """Based on your request, here's the analysis:

        The data shows:
        {"analysis": "positive", "confidence": 0.85, "keywords": ["good", "excellent",],}
        
        This indicates a positive sentiment.""",
    ]
    
    @classmethod
    def get_examples(cls) -> List[str]:
        return cls.COMMON_BROKEN_EXAMPLES

class StreamFixTester:
    """Tests StreamFix functionality"""
    
    def __init__(self, base_url: str = STREAMFIX_URL):
        self.base_url = base_url
        
    def test_health(self) -> bool:
        """Check if StreamFix is running"""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False
    
    def repair_json(self, broken_json: str) -> Dict[str, Any]:
        """Test JSON repair using the /test endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/test",
                json={"broken_json": broken_json},
                headers={"Content-Type": "application/json"}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def test_fsm_demo(self, text: str) -> Dict[str, Any]:
        """Test FSM processing using demo endpoint"""
        try:
            response = requests.post(
                f"{self.base_url}/v1/demo/fsm",
                json={"text": text, "content": text},
                headers={"Content-Type": "application/json"}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")

def print_test_result(original: str, result: Dict[str, Any]):
    """Print formatted test result"""
    print(f"\n📝 Original JSON:")
    print(f"   {original[:100]}{'...' if len(original) > 100 else ''}")
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
        
    if "repaired" in result:
        repaired = result.get("repaired", "")
        success = result.get("success", False)
        valid = result.get("valid_json", False)
        
        print(f"\n🔧 Repaired JSON:")
        print(f"   {repaired[:100]}{'...' if len(repaired) > 100 else ''}")
        print(f"\n✅ Status: {'SUCCESS' if success else 'FAILED'}")
        print(f"🧪 Valid JSON: {'YES' if valid else 'NO'}")
        
        if valid:
            try:
                parsed = json.loads(repaired)
                print(f"🎯 Parsed Successfully: {type(parsed).__name__} with {len(str(parsed))} characters")
            except:
                print(f"⚠️  Parse check failed")
    
    elif "processed" in result:
        processed = result.get("processed", "")
        fsm_applied = result.get("fsm_applied", False)
        
        print(f"\n🔧 FSM Processed:")
        print(f"   {processed[:100]}{'...' if len(processed) > 100 else ''}")
        print(f"\n🎯 FSM Applied: {'YES' if fsm_applied else 'NO'}")

def main():
    """Run comprehensive StreamFix workflow test"""
    
    print_header("StreamFix Production Workflow Test")
    print("🚀 Testing StreamFix without requiring API keys...")
    print("💰 This test is completely FREE - no external API calls!")
    
    # Initialize tester
    tester = StreamFixTester()
    
    # Test health
    print("\n🏥 Health Check...")
    if tester.test_health():
        print("✅ StreamFix is running and healthy!")
    else:
        print("❌ StreamFix is not accessible!")
        return
    
    # Get broken JSON examples
    examples = LLMSimulator.get_examples()
    
    print_header("Testing Common LLM JSON Issues")
    print(f"🧪 Testing {len(examples)} real-world scenarios...")
    
    success_count = 0
    
    for i, broken_json in enumerate(examples, 1):
        print(f"\n{'─'*60}")
        print(f"🧪 Test {i}/{len(examples)}: {['Trailing Commas', 'Missing Quotes', 'Mixed Quotes', 'Unescaped Strings', 'Incomplete Objects', 'Multiple JSON in Text', 'Complex Nested Issues', 'LLM Explanation with JSON'][i-1] if i <= 8 else 'Custom Test'}")
        
        # Test with main repair endpoint
        result = tester.repair_json(broken_json)
        print_test_result(broken_json, result)
        
        if result.get("valid_json"):
            success_count += 1
    
    print_header("Demo FSM Processing Test")
    print("🧪 Testing pure FSM processing (no repair logic)...")
    
    test_text = 'Here is some data: {"test": true, "items": [1,2,3,],}'
    fsm_result = tester.test_fsm_demo(test_text)
    print_test_result(test_text, fsm_result)
    
    print_header("Test Summary")
    print(f"📊 Results:")
    print(f"   ✅ Successful repairs: {success_count}/{len(examples)}")
    print(f"   📈 Success rate: {(success_count/len(examples)*100):.1f}%")
    print(f"   🌐 Production URL: {STREAMFIX_URL}")
    print(f"   💰 Total cost: $0.00 (No API keys needed!)")
    
    print_header("How to Use StreamFix in Your App")
    print("""
🔧 Integration Steps:

1. **Replace your OpenAI endpoint:**
   OLD: https://api.openai.com/v1/chat/completions
   NEW: https://streamfix.up.railway.app/v1/chat/completions
   
2. **Add StreamFix headers to your requests:**
   X-StreamFix-Target: https://api.openai.com/v1/chat/completions
   Authorization: Bearer YOUR_OPENAI_KEY
   
3. **StreamFix will:**
   ✅ Forward your request to OpenAI
   ✅ Stream the response back to you
   ✅ Automatically repair any broken JSON
   ✅ Add X-StreamFix-Request-Id for result retrieval

4. **Get repair details:**
   GET https://streamfix.up.railway.app/result/YOUR_REQUEST_ID
   
5. **Test without API keys:**
   POST https://streamfix.up.railway.app/test
   Body: {"broken_json": "your broken json here"}

🎯 That's it! StreamFix is a drop-in replacement that makes your LLM JSON bulletproof!
    """)

if __name__ == "__main__":
    main()