# API Reference

StreamFix provides an OpenAI-compatible API with JSON repair and optional schema validation.

## Endpoints

### Chat Completions
`POST /v1/chat/completions`

Standard OpenAI format + optional schema validation:

```json
{
  "model": "gpt-4",
  "messages": [{"role": "user", "content": "Return JSON"}],
  "schema": {
    "type": "object",
    "properties": {"name": {"type": "string"}},
    "required": ["name"]
  }
}
```

**Response includes**: `x-streamfix-request-id` header for artifact retrieval.

### Repair Artifacts
`GET /result/{request_id}`

Get detailed repair information:

```json
{
  "request_id": "req_abc123",
  "extracted_json": "{\"repaired\": true}",
  "extraction_status": "DONE",
  "repaired_content": "{\"repaired\": true}",
  "repairs_applied": ["remove_trailing_comma"],
  "parse_success": true,
  "status": "REPAIRED",
  "schema_valid": true,
  "schema_errors": []
}
```

### Health & Metrics
- `GET /health` - Server health status
- `GET /metrics` - Usage statistics and repair rates

## Schema Validation (Contract Mode)

When `schema` is provided, StreamFix:
1. **Extracts JSON** from mixed content (prose, code blocks, think tags)
2. **Repairs broken JSON** automatically
3. **Validates against schema** with detailed error messages
4. **Returns status** via artifact system

Status values:
- `PASSTHROUGH` - No repair needed, valid JSON
- `REPAIRED` - JSON repaired and valid
- `SCHEMA_INVALID` - Valid JSON but fails schema validation  
- `EXTRACTION_FAILED` - Could not extract/parse JSON

## Error Handling

StreamFix maintains OpenAI-compatible error responses while adding repair capabilities.
}
```

#### Response Headers
```
x-streamfix-request-id: req_abc123def456
content-type: application/json
```

#### Response Body
Standard OpenAI chat completion response:
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1640995200,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "{\"name\": \"John Doe\", \"email\": \"john@example.com\"}"
      },
      "finish_reason": "stop"
    }
  ]
}
```

### GET `/result/{request_id}`

Retrieve detailed repair and validation information for a specific request.

#### Response
```json
{
  "request_id": "req_abc123def456",
  "timestamp": "2025-12-14T10:30:00Z",
  "model": "gpt-4",
  "original_content": "raw model output...",
  "extracted_json": "{\"name\": \"John Doe\", \"email\": \"john@example.com\"}",
  "extraction_status": "DONE",
  "repaired_content": "{\"name\": \"John Doe\", \"email\": \"john@example.com\"}",
  "repairs_applied": [],
  "parse_success": true,
  "status": "PASSTHROUGH",
  "schema_provided": true,
  "schema_valid": true,
  "schema_errors": []
}
```

#### Status Values
- `PASSTHROUGH`: No repairs needed
- `REPAIRED`: JSON was fixed
- `SCHEMA_INVALID`: Failed schema validation
- `EXTRACTION_FAILED`: Could not extract JSON

#### Extraction Status
- `DONE`: JSON successfully extracted
- `TRUNCATED`: Partial JSON extracted
- `FAILED`: No JSON found

### GET `/metrics`

Get usage statistics and repair patterns.

#### Response
```json
{
  "total_requests": 1250,
  "repair_rate": 0.18,
  "parse_success_rate": 0.97,
  "repair_types": {
    "remove_trailing_comma": 45,
    "quote_unquoted_keys": 32,
    "fix_truncated_json": 12,
    "escape_quotes": 8
  },
  "last_updated": "2025-12-14T10:30:00Z"
}
```

### GET `/health`

Health check endpoint.

#### Response
```json
{
  "status": "healthy",
  "timestamp": "2025-12-14T10:30:00Z",
  "version": "1.0.0"
}
```

## Schema Validation

### Supported Schema Features

- **JSON Schema Draft 7** compatible
- **Type validation**: `string`, `number`, `integer`, `boolean`, `array`, `object`
- **Format validation**: `email`, `uri`, `date-time`, etc.
- **Constraints**: `minimum`, `maximum`, `minLength`, `maxLength`, `pattern`
- **Required fields**: Specify mandatory properties
- **Additional properties**: Control whether extra fields are allowed

### Example Schemas

#### Simple Object
```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "age": {"type": "integer", "minimum": 0}
  },
  "required": ["name"]
}
```

#### Nested Object
```json
{
  "type": "object",
  "properties": {
    "user": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "profile": {
          "type": "object", 
          "properties": {
            "email": {"type": "string", "format": "email"}
          }
        }
      }
    }
  }
}
```

#### Array Validation
```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "integer"},
          "name": {"type": "string"}
        },
        "required": ["id", "name"]
      }
    }
  }
}
```

### Error Messages

Schema validation errors include detailed paths and suggestions:
```json
{
  "schema_errors": [
    "Schema violation at 'user → email': 'invalid-email' is not a 'email' (expected format: email)",
    "💡 Ensure the value matches email format"
  ]
}
```

## Streaming

StreamFix supports Server-Sent Events (SSE) streaming:

#### Request
```json
{
  "model": "gpt-4",
  "messages": [...],
  "stream": true,
  "schema": {...}  // Optional
}
```

#### Response Stream
```
data: {"id":"chatcmpl-abc","object":"chat.completion.chunk",...}

data: {"id":"chatcmpl-abc","object":"chat.completion.chunk",...}

data: [DONE]
```

After the stream completes, the repair artifact is available via the `/result/{request_id}` endpoint.

## Error Handling

### Standard HTTP Status Codes
- `200`: Success
- `400`: Bad Request (invalid schema, malformed JSON)
- `404`: Request ID not found (for `/result` endpoint)
- `500`: Internal Server Error
- `502`: Upstream API error

### Error Response Format
```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "Invalid JSON schema provided: Additional properties are not allowed",
    "code": "invalid_schema"
  }
}
```

## Rate Limiting

StreamFix inherits rate limiting from your configured upstream API. No additional limits are imposed.

## Timeouts

- **Request timeout**: 60 seconds (configurable)
- **Streaming timeout**: No limit (follows upstream)
- **Artifact retention**: 100 most recent requests (in-memory)

## CORS

CORS headers are configured to allow browser requests:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
```