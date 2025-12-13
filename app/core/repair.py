import re
import json
from app.core.fsm import JsonFsmState

def fix_unquoted_keys(json_text: str) -> str:
    """Fix unquoted property names: {name: "value"} → {"name": "value"}"""
    # Use regex to find unquoted keys followed by colon
    # Pattern: word at start of line/after brace/comma, followed by colon
    
    def quote_key(match):
        before = match.group(1)  # whitespace/brace/comma before
        key = match.group(2)     # the unquoted key
        after = match.group(3)   # whitespace and colon after
        return f'{before}"{key}"{after}'
    
    # Match: (whitespace/brace/comma)(word)(whitespace:)
    pattern = r'([{\s,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)'
    return re.sub(pattern, quote_key, json_text)

def fix_quote_types(json_text: str) -> str:
    """Fix single quotes to double quotes: {'key': 'value'} → {"key": "value"}"""
    # Simple replacement - just swap all single quotes with double quotes
    # This works for most cases where single quotes are used consistently
    return json_text.replace("'", '"')

def fix_unescaped_quotes(json_text: str) -> str:
    """Try to fix unescaped quotes in string values"""
    # First, check if it already parses - if so, don't touch it
    try:
        import json
        json.loads(json_text)
        return json_text
    except:
        pass
    
    # Look for key-value pairs where the value contains unescaped quotes
    # Pattern: "key": "value with "quotes" inside"
    pattern = r'"[^"]*":\s*"[^"]*"[^"]*"[^"]*"'
    
    def fix_kv_pair(match):
        kv_pair = match.group(0)
        colon_pos = kv_pair.find(':')
        
        if colon_pos == -1:
            return kv_pair
        
        key_part = kv_pair[:colon_pos+1]
        value_part = kv_pair[colon_pos+1:].strip()
        
        # Fix the value part if it has the quote pattern
        if value_part.startswith('"') and value_part.endswith('"') and value_part.count('"') > 2:
            inner = value_part[1:-1]  # Remove outer quotes
            # Escape any unescaped quotes in the inner content
            inner_fixed = inner.replace('"', '\\"')
            value_fixed = f'"{inner_fixed}"'
            return key_part + ' ' + value_fixed
        
        return kv_pair
    
    result = re.sub(pattern, fix_kv_pair, json_text)
    
    # Test if our fix worked
    if result != json_text:
        try:
            json.loads(result)
            return result
        except:
            # Our fix didn't work, return original
            pass
    
    return json_text

def safe_repair(json_text: str, state: JsonFsmState = None) -> str:
    """
    Enhanced JSON repair:
    - fix unquoted property names
    - fix single quotes to double quotes
    - escape unescaped quotes in strings
    - remove trailing commas in objects/arrays
    - close missing brackets for truncated JSON
    - handle incomplete values
    """
    if not json_text:
        return json_text
    
    # 1. Fix unquoted property names: {name: "value"} → {"name": "value"}
    # Match word characters followed by colon (but not inside strings)
    json_text = fix_unquoted_keys(json_text)
    
    # 2. Fix single quotes to double quotes: {'key': 'value'} → {"key": "value"}
    json_text = fix_quote_types(json_text)
    
    # 3. Try to fix unescaped quotes in string values
    json_text = fix_unescaped_quotes(json_text)
    
    # 4. Remove trailing commas: { "a": 1, } or [1,2,]
    json_text = re.sub(r",\s*([}\]])", r"\1", json_text)
    
    # 5. Handle truncated JSON if state is provided
    if state and state.state != "DONE" and state.depth > 0:
        # Handle incomplete string values by closing quotes
        if state.in_string and not json_text.endswith('"'):
            json_text += '"'
        
        # Handle incomplete boolean/null values at the end
        # Look for partial keywords and complete them
        if re.search(r'\b(tru)$', json_text):
            json_text = re.sub(r'\b(tru)$', 'true', json_text)
        elif re.search(r'\b(fals)$', json_text):
            json_text = re.sub(r'\b(fals)$', 'false', json_text)
        elif re.search(r'\b(nul)$', json_text):
            json_text = re.sub(r'\b(nul)$', 'null', json_text)
        else:
            # Handle incomplete values - remove key:value pairs where value is incomplete
            # Pattern: "key": partial_value (where partial_value is not a complete JSON value)
            json_text = re.sub(r'"\w+":\s*[a-zA-Z]+$', '', json_text)
            json_text = re.sub(r',\s*$', '', json_text)  # Remove trailing comma after removal
        
        # Count what actually needs closing and close in correct order
        # We need to close structures in LIFO order (last opened first)
        
        # Build a stack of what's open by scanning the string
        stack = []
        i = 0
        in_string = False
        escape = False
        
        while i < len(json_text):
            char = json_text[i]
            
            if in_string:
                if escape:
                    escape = False
                elif char == '\\':
                    escape = True
                elif char == '"':
                    in_string = False
            else:
                if char == '"':
                    in_string = True
                elif char == '{':
                    stack.append('}')
                elif char == '[':
                    stack.append(']')
                elif char in '}]':
                    if stack and stack[-1] == char:
                        stack.pop()
            
            i += 1
        
        # Close everything still on the stack
        json_text += ''.join(reversed(stack))
    
    return json_text


def attempt_json_parse(json_text: str) -> tuple[bool, dict, str]:
    """
    Attempt to parse JSON text.
    Returns (success, parsed_obj_or_empty, error_msg)
    """
    try:
        obj = json.loads(json_text)
        return True, obj, ""
    except json.JSONDecodeError as e:
        return False, {}, str(e)
    except Exception as e:
        return False, {}, str(e)