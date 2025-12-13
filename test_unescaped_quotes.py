#!/usr/bin/env python3
"""
Test the unescaped quotes fix specifically
"""
import sys
import json
sys.path.append('/Users/antonzaytsev/Documents/win-andr')

from app.core.repair import fix_unescaped_quotes, safe_repair, attempt_json_parse

def test_unescaped_quotes():
    test_cases = [
        '{"message": "He said "Hello" to me"}',
        '{"message": "He said "Hello world" to everyone", "status": "ok"}',
        '{"text": "She replied "I agree" and left"}',
        '{"quote": "The sign said "No Entry" clearly"}',
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*50}")
        print(f"Input: {test_case}")
        
        # Test step by step
        step1 = fix_unescaped_quotes(test_case)
        print(f"After fix_unescaped_quotes: {step1}")
        
        # Test full repair
        repaired = safe_repair(test_case)
        print(f"Full repair result: {repaired}")
        
        # Test if it parses
        success, obj, error = attempt_json_parse(repaired)
        print(f"Parses successfully: {success}")
        if not success:
            print(f"Error: {error}")
        else:
            print(f"✅ SUCCESS!")

if __name__ == "__main__":
    test_unescaped_quotes()