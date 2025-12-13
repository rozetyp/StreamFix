#!/usr/bin/env python3
import re

# Test the pattern matching
test = '{"message": "He said "Hello" to me"}'
print(f"Input: {test}")

pattern = r'"[^"\\]*"[^"\\]*"[^"]*"'
matches = re.findall(pattern, test)
print(f"Pattern matches: {matches}")

# Try a simpler pattern
pattern2 = r'"[^"]*"[^"]*"[^"]*"'
matches2 = re.findall(pattern2, test)
print(f"Simpler pattern matches: {matches2}")

# Let's manually find the problem
# {"message": "He said "Hello" to me"}
#             ^      ^      ^         ^
#             1      2      3         4

# The issue is we have 4 quotes total, and we want to escape quotes 2 and 3
# But this happens inside the VALUE of a key-value pair

# New approach: find key-value pairs where the value has unescaped quotes
pattern3 = r'"[^"]*":\s*"[^"]*"[^"]*"[^"]*"'
matches3 = re.findall(pattern3, test)
print(f"Key-value pattern matches: {matches3}")

if matches3:
    print("Found match!")
    match = matches3[0]
    print(f"Match: {match}")
    
    # Find the colon to separate key from value
    colon_pos = match.find(':')
    key_part = match[:colon_pos+1]
    value_part = match[colon_pos+1:].strip()
    
    print(f"Key part: {key_part}")
    print(f"Value part: {value_part}")
    
    # Now fix the value part
    if value_part.startswith('"') and value_part.endswith('"'):
        inner = value_part[1:-1]  # Remove outer quotes
        # Escape any unescaped quotes in the inner content
        inner_fixed = inner.replace('"', '\\"')
        value_fixed = f'"{inner_fixed}"'
        
        result = key_part + ' ' + value_fixed
        print(f"Fixed: {result}")
        
        # Test in context
        import json
        full_fixed = test.replace(match, result)
        print(f"Full fixed: {full_fixed}")
        
        try:
            json.loads(full_fixed)
            print("✅ SUCCESS! Parses correctly")
        except Exception as e:
            print(f"❌ Still fails: {e}")