"""
Unit tests for JSON Schema validation functionality
"""
import pytest
import json
from app.core.schema_validator import (
    validate_against_schema,
    is_valid_schema,
    extract_schema_requirements,
    generate_schema_description,
    EXAMPLE_SCHEMAS
)


class TestSchemaValidation:
    """Test schema validation functionality"""
    
    def test_valid_json_against_schema(self):
        """Test valid JSON passes schema validation"""
        json_data = '{"name": "John", "age": 30}'
        schema = EXAMPLE_SCHEMAS["person"]
        
        is_valid, errors = validate_against_schema(json_data, schema)
        
        assert is_valid is True
        assert errors == []
    
    def test_invalid_json_syntax(self):
        """Test invalid JSON syntax is caught"""
        json_data = '{"name": "John", "age": 30,}'  # trailing comma
        schema = EXAMPLE_SCHEMAS["person"]
        
        is_valid, errors = validate_against_schema(json_data, schema)
        
        assert is_valid is False
        assert len(errors) == 1
        assert "Invalid JSON syntax" in errors[0]
    
    def test_missing_required_field(self):
        """Test missing required field is caught"""
        json_data = '{"name": "John"}'  # missing age
        schema = EXAMPLE_SCHEMAS["person"]
        
        is_valid, errors = validate_against_schema(json_data, schema)
        
        assert is_valid is False
        assert len(errors) == 1
        assert "age" in errors[0]
    
    def test_wrong_type(self):
        """Test wrong field type is caught"""
        json_data = '{"name": "John", "age": "thirty"}'  # age should be integer
        schema = EXAMPLE_SCHEMAS["person"]
        
        is_valid, errors = validate_against_schema(json_data, schema)
        
        assert is_valid is False
        assert len(errors) == 1
        assert "age" in errors[0] or "integer" in errors[0]
    
    def test_extra_fields_allowed(self):
        """Test extra fields are allowed by default"""
        json_data = '{"name": "John", "age": 30, "city": "NYC"}'
        schema = EXAMPLE_SCHEMAS["person"]
        
        is_valid, errors = validate_against_schema(json_data, schema)
        
        assert is_valid is True
        assert errors == []
    
    def test_array_validation(self):
        """Test array schema validation"""
        json_data = '["apple", "banana", "orange"]'
        schema = EXAMPLE_SCHEMAS["simple_list"]
        
        is_valid, errors = validate_against_schema(json_data, schema)
        
        assert is_valid is True
        assert errors == []
    
    def test_invalid_array_items(self):
        """Test invalid array items are caught"""
        json_data = '["apple", 123, "orange"]'  # 123 should be string
        schema = EXAMPLE_SCHEMAS["simple_list"]
        
        is_valid, errors = validate_against_schema(json_data, schema)
        
        assert is_valid is False
        assert len(errors) == 1


class TestSchemaUtilities:
    """Test schema utility functions"""
    
    def test_valid_schema_check(self):
        """Test valid schema is recognized"""
        schema = EXAMPLE_SCHEMAS["person"]
        
        is_valid, error = is_valid_schema(schema)
        
        assert is_valid is True
        assert error == ""
    
    def test_invalid_schema_check(self):
        """Test invalid schema is caught"""
        invalid_schema = {"type": "invalid_type"}
        
        is_valid, error = is_valid_schema(invalid_schema)
        
        assert is_valid is False
        assert error != ""
    
    def test_extract_requirements_object(self):
        """Test extracting requirements from object schema"""
        schema = EXAMPLE_SCHEMAS["person"]
        
        requirements = extract_schema_requirements(schema)
        
        assert "Required fields: name, age" in requirements
        assert "name: string" in requirements
        assert "age: integer" in requirements
    
    def test_extract_requirements_array(self):
        """Test extracting requirements from array schema"""
        schema = EXAMPLE_SCHEMAS["simple_list"]
        
        requirements = extract_schema_requirements(schema)
        
        assert "Must be an array" in requirements
        assert "Array items must be: string" in requirements
    
    def test_generate_description_object(self):
        """Test generating description for object schema"""
        schema = EXAMPLE_SCHEMAS["person"]
        
        description = generate_schema_description(schema)
        
        assert "Object with 3 properties (2 required)" == description
    
    def test_generate_description_array(self):
        """Test generating description for array schema"""
        schema = EXAMPLE_SCHEMAS["simple_list"]
        
        description = generate_schema_description(schema)
        
        assert "Array of string" == description


class TestRealWorldScenarios:
    """Test with real-world JSON scenarios"""
    
    def test_complex_nested_object(self):
        """Test complex nested object validation"""
        json_data = '''{
            "id": "prod_123",
            "price": 29.99,
            "tags": ["electronics", "mobile"]
        }'''
        
        schema = EXAMPLE_SCHEMAS["product"]
        
        is_valid, errors = validate_against_schema(json_data, schema)
        
        assert is_valid is True
        assert errors == []
    
    def test_malformed_json_from_ai(self):
        """Test typical AI-generated malformed JSON"""
        # This would be fixed by our repair logic first, then validated
        json_data = '{"id": "prod_123", "price": 29.99}'  # missing tags, but not required
        
        schema = EXAMPLE_SCHEMAS["product"]
        
        is_valid, errors = validate_against_schema(json_data, schema)
        
        assert is_valid is True  # tags not required
        assert errors == []
    
    def test_ai_json_with_extra_content(self):
        """Test JSON with extra AI explanation content"""
        # This would be extracted by our FSM first
        json_data = '{"name": "John", "age": 30}'
        
        schema = EXAMPLE_SCHEMAS["person"]
        
        is_valid, errors = validate_against_schema(json_data, schema)
        
        assert is_valid is True
        assert errors == []


if __name__ == "__main__":
    # Quick manual test
    print("Testing schema validation...")
    
    # Test valid case
    valid_json = '{"name": "Test User", "age": 25}'
    schema = EXAMPLE_SCHEMAS["person"]
    is_valid, errors = validate_against_schema(valid_json, schema)
    print(f"Valid JSON: {is_valid}, Errors: {errors}")
    
    # Test invalid case
    invalid_json = '{"name": "Test User"}'  # missing age
    is_valid, errors = validate_against_schema(invalid_json, schema)
    print(f"Invalid JSON: {is_valid}, Errors: {errors}")
    
    print("Schema validation tests completed!")