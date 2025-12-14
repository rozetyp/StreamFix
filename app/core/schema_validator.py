"""
JSON Schema validation for Contract Mode
Provides schema validation functionality for guaranteed JSON structure
"""
import json
import jsonschema
from typing import Dict, Any, Tuple, Optional, List


def validate_against_schema(json_data: str, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate JSON string against provided JSON schema
    
    Args:
        json_data: JSON string to validate
        schema: JSON schema dictionary
        
    Returns:
        Tuple of (is_valid, detailed_error_messages)
    """
    try:
        # First check if JSON is parseable
        parsed_data = json.loads(json_data)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON syntax at line {e.lineno}, column {e.colno}: {e.msg}"]
    
    try:
        # Validate against schema
        jsonschema.validate(parsed_data, schema)
        return True, []
    except jsonschema.ValidationError as e:
        # Extract detailed error information
        error_messages = []
        
        # Build path to error location
        error_path = " → ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
        
        # Enhanced error message with context
        main_error = f"Schema violation at '{error_path}': {e.message}"
        
        # Add schema requirements context
        if e.schema:
            expected_type = e.schema.get("type")
            if expected_type:
                main_error += f" (expected type: {expected_type})"
                
            # Add format requirements if present
            expected_format = e.schema.get("format")
            if expected_format:
                main_error += f" (expected format: {expected_format})"
                
            # Add required fields if this is a missing property error
            if "required" in e.schema and e.validator == "required":
                required_fields = e.schema["required"]
                main_error += f" (required fields: {', '.join(required_fields)})"
        
        error_messages.append(main_error)
        
        # Add helpful suggestions based on error type
        if e.validator == "type":
            error_messages.append(f"💡 Try converting the value to {e.schema.get('type', 'correct')} type")
        elif e.validator == "required":
            missing_props = set(e.schema.get("required", [])) - set(e.instance.keys())
            error_messages.append(f"💡 Add missing properties: {', '.join(missing_props)}")
        elif e.validator == "format":
            error_messages.append(f"💡 Ensure the value matches {e.schema.get('format')} format")
        
        return False, error_messages
    except jsonschema.SchemaError as e:
        return False, [f"Invalid schema provided: {str(e)}"]


def is_valid_schema(schema: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check if provided schema is a valid JSON schema
    
    Args:
        schema: Schema dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        jsonschema.Draft7Validator.check_schema(schema)
        return True, ""
    except jsonschema.SchemaError as e:
        return False, str(e)


def extract_schema_requirements(schema: Dict[str, Any]) -> str:
    """
    Extract human-readable requirements from JSON schema for retry prompts
    
    Args:
        schema: JSON schema dictionary
        
    Returns:
        Human-readable description of schema requirements
    """
    requirements = []
    
    if schema.get("type") == "object":
        # Required fields
        required_fields = schema.get("required", [])
        if required_fields:
            requirements.append(f"Required fields: {', '.join(required_fields)}")
        
        # Field types
        properties = schema.get("properties", {})
        if properties:
            field_types = []
            for field, field_schema in properties.items():
                field_type = field_schema.get("type", "any")
                field_types.append(f"{field}: {field_type}")
            requirements.append(f"Field types: {', '.join(field_types)}")
    
    elif schema.get("type") == "array":
        requirements.append("Must be an array")
        items_schema = schema.get("items")
        if items_schema and isinstance(items_schema, dict):
            item_type = items_schema.get("type", "any")
            requirements.append(f"Array items must be: {item_type}")
    
    else:
        schema_type = schema.get("type", "object")
        requirements.append(f"Must be type: {schema_type}")
    
    return ". ".join(requirements) if requirements else "Follow the provided JSON structure"


def generate_schema_description(schema: Dict[str, Any]) -> str:
    """
    Generate a concise description of the schema for logging/artifacts
    
    Args:
        schema: JSON schema dictionary
        
    Returns:
        Brief description of the schema
    """
    schema_type = schema.get("type", "unknown")
    
    if schema_type == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        return f"Object with {len(properties)} properties ({len(required)} required)"
    
    elif schema_type == "array":
        items_type = schema.get("items", {}).get("type", "any")
        return f"Array of {items_type}"
    
    else:
        return f"Type: {schema_type}"


# Example schemas for testing
EXAMPLE_SCHEMAS = {
    "person": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0},
            "email": {"type": "string", "format": "email"}
        },
        "required": ["name", "age"]
    },
    "product": {
        "type": "object", 
        "properties": {
            "id": {"type": "string"},
            "price": {"type": "number", "minimum": 0},
            "tags": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["id", "price"]
    },
    "simple_list": {
        "type": "array",
        "items": {"type": "string"}
    }
}