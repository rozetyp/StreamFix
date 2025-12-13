import re
import json
from app.core.fsm import JsonFsmState

def safe_repair(json_text: str, state: JsonFsmState) -> str:
    """
    Very conservative repair:
    - close braces/brackets based on what's actually open in the text
    - remove trailing commas in objects/arrays
    - handle incomplete values
    """
    if not json_text:
        return json_text
    
    # remove trailing commas: { "a": 1, } or [1,2,]
    json_text = re.sub(r",\s*([}\]])", r"\1", json_text)
    
    # if truncated, try to repair
    if state.state != "DONE" and state.depth > 0:
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