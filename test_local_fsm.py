#!/usr/bin/env python3
"""
Local test to understand how StreamFix really works
"""
import sys
import json
sys.path.append('/Users/antonzaytsev/Documents/win-andr')

from app.core.fsm import PreprocessState, JsonFsmState, preprocess_complete, fsm_feed, fsm_result, fsm_finalize
from app.core.repair import safe_repair, attempt_json_parse

def test_trailing_commas():
    """Test how trailing comma repair works"""
    broken_json = '{"name": "John", "age": 30, "hobbies": ["reading", "coding",],}'
    
    print("🧪 Testing StreamFix FSM + Repair Pipeline")
    print(f"Input: {broken_json}")
    
    # Step 1: Preprocess (removes fences, think blocks)
    preprocessed = preprocess_complete(broken_json)
    print(f"Preprocessed: {preprocessed}")
    
    # Step 2: Extract JSON with FSM
    state = JsonFsmState()
    fsm_feed(state, preprocessed)
    fsm_finalize(state)  # Mark as complete
    extracted, status = fsm_result(state)
    
    print(f"Extracted: {extracted}")
    print(f"Status: {status}")
    
    # Step 3: Repair if needed
    if status in ["DONE", "TRUNCATED"]:
        repaired = safe_repair(extracted, state)
        print(f"Repaired: {repaired}")
        
        # Step 4: Validate
        success, obj, error = attempt_json_parse(repaired)
        print(f"Parse success: {success}")
        if success:
            print(f"Parsed object: {json.dumps(obj, indent=2)}")
        else:
            print(f"Parse error: {error}")
    
    return extracted, status

def test_fenced_json():
    """Test fenced JSON processing"""
    fenced = '''Here's the data:
```json
{"result": "success", "items": [1,2,3,]}
```
Some text after.'''
    
    print("\n🧪 Testing Fenced JSON")
    print(f"Input: {fenced}")
    
    # Step 1: Preprocess (should extract just the JSON)
    preprocessed = preprocess_complete(fenced)
    print(f"Preprocessed: {preprocessed}")
    
    # Step 2: Extract JSON with FSM  
    state = JsonFsmState()
    fsm_feed(state, preprocessed)
    fsm_finalize(state)
    extracted, status = fsm_result(state)
    
    print(f"Extracted: {extracted}")
    print(f"Status: {status}")
    
    # Step 3: Repair
    if status in ["DONE", "TRUNCATED"]:
        repaired = safe_repair(extracted, state)
        print(f"Repaired: {repaired}")
        
        success, obj, error = attempt_json_parse(repaired)
        print(f"Parse success: {success}")
        if success:
            print(f"Result: {obj}")

if __name__ == "__main__":
    test_trailing_commas()
    test_fenced_json()