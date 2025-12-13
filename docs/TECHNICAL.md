# StreamFix Technical Documentation

## Architecture

StreamFix is a **stateless HTTP proxy** that provides JSON repair for AI streaming APIs:

```
Client ──→ StreamFix Gateway ──→ OpenRouter API
   ↑              │                    │
   └──────── JSON-repaired ←──────────┘
                response
```

### Core Components

- **FSM Parser**: Real-time JSON extraction from mixed content
- **Repair Engine**: Safe fixes for trailing commas, unquoted keys, bracket completion
- **Stream Processor**: SSE handling with chunk boundary safety
- **OpenRouter Integration**: Multi-model API access (Claude, GPT, 100+ models)

### Key Files

- `app/main.py` - FastAPI application entry point
- `app/core/fsm.py` - JSON extraction finite state machine
- `app/core/repair.py` - Safe JSON repair algorithms
- `app/api/chat_noauth.py` - OpenAI-compatible proxy endpoint
- `app/core/stream_processor.py` - Streaming response handler

## Testing

**Unit Tests**: `python -m pytest tests/` (29 tests covering FSM and repair logic)

**Manual Testing**:
```bash
# Non-streaming repair test
curl -X POST https://streamfix.up.railway.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": "Return: {\"test\": true,}"}]}'

# Streaming test  
curl -X POST https://streamfix.up.railway.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "anthropic/claude-3-haiku", "stream": true, "messages": [{"role": "user", "content": "Count to 3"}]}'
```

## Validated Capabilities

✅ **Content Extraction**: `<think>` blocks, markdown fences, mixed content  
✅ **JSON Repair**: Trailing commas, unquoted keys, bracket completion  
✅ **Streaming Safety**: SSE protocol with chunk boundary handling  
✅ **Multi-Provider**: OpenRouter integration working  
✅ **Request Tracking**: x-streamfix-request-id headers  
✅ **Repair Artifacts**: /result/{id} endpoint for debugging  
✅ **Metrics**: /metrics endpoint for observability  

## Supported JSON Issues

### **Content Wrappers** (automatically extracted)
- `<think>reasoning</think>` blocks before/around JSON
- Markdown code fences: ```json ... ``` or ``` ... ```
- Prose text mixed with JSON responses
- Tool-call wrappers with embedded JSON payloads

### **JSON Malformations** (automatically repaired)
- **Trailing commas**: `{"test": true,}` → `{"test": true}`
- **Unquoted keys**: `{name: "value"}` → `{"name": "value"}`
- **Single quotes**: `{'key': 'value'}` → `{"key": "value"}`
- **Missing brackets**: `{"data": [1,2` → `{"data": [1,2]}`
- **Incomplete keywords**: `{"flag": tru` → `{"flag": true}`

### **Streaming Edge Cases** (safely handled)
- Chunk boundaries splitting JSON tokens
- Chunk boundaries inside `<think>` tags or code fences
- SSE `data:` event parsing and `[DONE]` termination
- Delta content extraction from streaming responses

### **What We DON'T Fix**
- Complex string corruption requiring semantic understanding
- Schema violations (wrong types, missing fields)
- JSON5 syntax (comments, hex numbers, NaN/Infinity)
- Malformed escape sequences

For edge cases we can't repair, the repair artifacts provide detailed diagnostics for implementing retry logic.  

## Deployment

**Railway**: https://streamfix.up.railway.app  
**Environment**: Set `OPENROUTER_API_KEY` environment variable  
**Docker**: Standard FastAPI deployment pattern  

## JSON Repair Technology

StreamFix uses a **finite state machine** that tracks parsing context in real-time:

- **String Context**: Handles escaping, prevents corruption inside quotes
- **Nesting Depth**: Tracks `{` and `[` for auto-completion
- **Safe Repairs**: Only applies fixes when structurally safe
- **Content Filtering**: Removes reasoning blocks, extracts from code fences

**Example Repairs**:
- `{"test": true,}` → `{"test": true}` (trailing comma)
- `{name: "value"}` → `{"name": "value"}` (unquoted keys)
- `{"data": [1,2` → `{"data": [1,2]}` (bracket completion)

This approach handles **any malformation pattern** automatically, not just pre-built scenarios.