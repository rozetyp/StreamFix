#!/usr/bin/env python3
"""
Test the enhanced repair function locally
"""
import sys
import json
sys.path.append('/Users/antonzaytsev/Documents/win-andr')

from app.core.fsm import JsonFsmState
from app.core.repair import safe_repair, attempt_json_parse

def test_enhanced_repair():
    """Test cases for the enhanced repair function"""
    test_cases = [
        # Test 1: Unquoted property names
        '{name: "John", age: 30}',
        
        # Test 2: Single quotes
        "{'name': 'John', 'age': 30}",
        
        # Test 3: Mixed issues
        '{name: "John", age: 30, "hobbies": ["reading", "coding",],}',
        
        # Test 4: Unescaped quotes (simple case)
        '{"message": "He said "Hello" to me"}',
        
        # Test 5: Complex nested with multiple issues
        '''{
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
}'''
    ]
    
    for i, broken_json in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {['Unquoted Keys', 'Single Quotes', 'Mixed Issues', 'Unescaped Quotes', 'Complex Nested'][i-1]}")
        print(f"Input: {broken_json}")
        
        # Test original parse
        success_orig, _, error_orig = attempt_json_parse(broken_json)
        print(f"Original parses: {success_orig} (error: {error_orig if not success_orig else 'none'})")
        
        # Apply repair
        repaired = safe_repair(broken_json)
        print(f"Repaired: {repaired}")
        
        # Test repaired parse
        success_rep, obj, error_rep = attempt_json_parse(repaired)
        print(f"Repaired parses: {success_rep}")
        if success_rep:
            print(f"✅ SUCCESS! Parsed object keys: {list(obj.keys()) if isinstance(obj, dict) else 'array'}")
        else:
            print(f"❌ FAILED: {error_rep}")

if __name__ == "__main__":
    test_enhanced_repair()