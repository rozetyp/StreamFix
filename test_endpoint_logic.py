#!/usr/bin/env python3
"""
Test the fixed streamfix endpoint logic locally
"""
import sys
import json
sys.path.append('/Users/antonzaytsev/Documents/win-andr')

from app.core.fsm import PreprocessState, JsonFsmState, preprocess_chunk, preprocess_finalize, fsm_feed, fsm_result, fsm_finalize
from app.core.repair import safe_repair, attempt_json_parse

def test_streamfix_endpoint_logic(broken_json: str):
    """Simulate the exact logic from /test endpoint"""
    
    print(f"Testing: {broken_json}")
    
    try:
        # Try to parse original (should fail)
        original_valid = True
        try:
            json.loads(broken_json)
        except json.JSONDecodeError:
            original_valid = False
        
        if original_valid:
            print("✅ JSON is already valid")
            return {
                "success": True,
                "original": broken_json,
                "repaired": broken_json,
                "valid_json": True,
                "error": "Input JSON was already valid"
            }
        
        # Use StreamFix FSM to repair the JSON
        preproc_state = PreprocessState()
        fsm_state = JsonFsmState()
        
        # Process the broken JSON through FSM
        for chunk in [broken_json]:  # Single chunk for testing
            extracted = preprocess_chunk(chunk, preproc_state)
            if extracted:
                fsm_feed(fsm_state, extracted)
        
        # Finalize preprocessing and FSM
        final_extracted = preprocess_finalize(preproc_state)
        if final_extracted:
            fsm_feed(fsm_state, final_extracted)
        
        fsm_finalize(fsm_state)
        extracted_json, fsm_status = fsm_result(fsm_state)
        
        print(f"FSM extracted: {extracted_json}")
        print(f"FSM status: {fsm_status}")
        
        # Apply repair to extracted JSON
        if fsm_status in ["DONE", "TRUNCATED"] and extracted_json.strip():
            repaired_json = safe_repair(extracted_json, fsm_state)
        else:
            # Fallback to direct repair on original text
            repaired_json = safe_repair(broken_json)
        
        print(f"Repaired: {repaired_json}")
        
        # Test if repaired JSON is valid
        valid_json = True
        error = None
        try:
            json.loads(repaired_json)
        except json.JSONDecodeError as e:
            valid_json = False
            error = f"Repair failed: {str(e)}"
        
        return {
            "success": valid_json,
            "original": broken_json,
            "repaired": repaired_json,
            "valid_json": valid_json,
            "error": error
        }
        
    except Exception as e:
        return {
            "success": False,
            "original": broken_json,
            "repaired": "",
            "valid_json": False,
            "error": f"Processing error: {str(e)}"
        }

if __name__ == "__main__":
    test_cases = [
        '{"name": "John", "age": 30, "hobbies": ["reading", "coding",],}',
        '{name: "John", age: 30}',
        '{"message": "He said "Hello" to me"}',
        '{"users": [{"id": 1}, {"id": 2}',
        '''```json
{"result": "success", "items": [1,2,3,]}
```'''
    ]
    
    for test_case in test_cases:
        print("=" * 60)
        result = test_streamfix_endpoint_logic(test_case)
        print(f"Result: {result}")
        print()