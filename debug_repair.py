#!/usr/bin/env python3
"""
Debug the repair functions step by step
"""
import sys
sys.path.append('/Users/antonzaytsev/Documents/win-andr')

from app.core.repair import fix_unquoted_keys, fix_quote_types, fix_unescaped_quotes

def debug_repairs():
    test_input = '{name: "John", age: 30}'
    print(f"Original: {test_input}")
    
    step1 = fix_unquoted_keys(test_input)
    print(f"After fix_unquoted_keys: {step1}")
    
    step2 = fix_quote_types(step1)
    print(f"After fix_quote_types: {step2}")
    
    step3 = fix_unescaped_quotes(step2)
    print(f"After fix_unescaped_quotes: {step3}")

if __name__ == "__main__":
    debug_repairs()