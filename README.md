# StreamFix

**OpenAI-compatible JSON repair proxy** - fixes broken LLM JSON automatically.

## ⚡ Quick Start (30 seconds)

### Option 1: Install & Run
```bash
pip install -e .
streamfix serve
# ✅ Running on http://localhost:8000/v1
```

### Option 2: Try Online
```bash
curl -X POST https://streamfix.up.railway.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": "broken JSON: {name: Alice,}"}]}'
```

## Usage

**Just change your `base_url` - everything else stays the same:**

```python
from openai import OpenAI

# Before: Broken JSON crashes your app
client = OpenAI(api_key="your-key")

# After: Always get valid JSON
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-key"
)
```

```javascript
const client = new OpenAI({
  baseURL: 'http://localhost:8000/v1',
  apiKey: 'your-key'
});
```

## Features

- ✅ **Fixes broken JSON** automatically (trailing commas, missing braces, etc.)
- ✅ **Schema validation** with detailed errors (Contract Mode)
- ✅ **Works with any provider** (OpenAI, Anthropic, local models)
- ✅ **Streaming compatible** (doesn't break SSE)
- ✅ **Local-first** (zero trust issues)

## Configuration

```bash
# Local models (default)
streamfix serve  # Uses localhost:1234

# With API key
streamfix serve --upstream https://api.openai.com/v1 --api-key YOUR_KEY

# Environment variable
export OPENROUTER_API_KEY=your-key
streamfix serve --upstream https://openrouter.ai/api/v1
```

## Schema Validation (Contract Mode)

Guarantee JSON matches your schema:

```python
response = client.chat.completions.create(
    model="gpt-4",
    schema={
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"]
    },
    messages=[{"role": "user", "content": "Extract name"}]
)

# Get validation details
request_id = response.headers["x-streamfix-request-id"] 
artifact = requests.get(f"http://localhost:8000/result/{request_id}").json()
print(f"Valid: {artifact['schema_valid']}")
```

## Self-Hosting

```bash
# Docker
docker run -p 8000:8000 -e OPENROUTER_API_KEY=key streamfix/gateway

# Railway (one-click)
# [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/streamfix)
```

## Endpoints

- `POST /v1/chat/completions` - OpenAI-compatible + optional `schema` field
- `GET /result/{request_id}` - Get repair/validation details  
- `GET /health` - Health check
- `GET /metrics` - Usage stats

**That's it.** StreamFix makes LLM JSON reliable with zero code changes.

---

**Full docs**: See `/docs/` folder for API reference, deployment guides, etc.
```bash
# Test the live demo
curl -X POST https://streamfix.up.railway.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": "Return: {\"test\": true,}"}]}'
```

[![Production](https://img.shields.io/badge/status-production_ready-green.svg)](https://streamfix.up.railway.app)
[![Parse Success](https://img.shields.io/badge/parse_success-100%25-brightgreen.svg)](#)
[![Models](https://img.shields.io/badge/models-100%2B_supported-blue.svg)](#)

---

## The Problem

Your agents crash at 2am because one bracket is missing. Your local models return beautiful explanations wrapped in broken JSON. Your workflows fail because trailing commas aren't "real JSON."

```javascript
// Your code today
const response = await openai.chat.completions.create({...});
const data = JSON.parse(response.content); // 💥 Crashes randomly
```

```json
❌ Model output: {"result": "success", "items": [1,2,3,],}  
❌ JSON.parse(): "Unexpected token '}'"
❌ Your automation: BROKEN
```

## The Solution

Change one line. Get parseable JSON every time.

```javascript
// With StreamFix
const client = new OpenAI({ baseURL: "https://streamfix.up.railway.app/v1" });
const response = await client.chat.completions.create({...});
const data = JSON.parse(response.content); // ✅ Always works
```

```json
✅ Model output: {"result": "success", "items": [1,2,3,],}
✅ StreamFix repair: {"result": "success", "items": [1,2,3]}  
✅ JSON.parse(): SUCCESS
✅ Your automation: RUNNING
```

---

## Perfect For

**🏠 Local Model Users** - Ollama, LM Studio, vLLM where JSON discipline varies  
**🔄 Multi-Provider Setups** - OpenRouter, multiple APIs, can't guarantee format consistency  
**🤖 Agent Builders** - LangChain, n8n, Zapier workflows that break on malformed JSON  
**⚡ Streaming Apps** - Real-time UX that needs reliable final artifacts  

---

## 60-Second Setup

**1. Test instantly** (no signup, no config):
```bash
curl https://streamfix.up.railway.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-3-haiku",
    "messages": [{"role": "user", "content": "Return broken JSON: {\"test\": true,}"}]
  }' -i | grep x-streamfix-request-id

# Get the request ID from the header, then:
curl https://streamfix.up.railway.app/result/req_YOUR_ID
```

**2. Point your existing code** at StreamFix:
```python
# Before: unreliable parsing
client = OpenAI()

# After: guaranteed parsing + repair insights
client = OpenAI(base_url="https://streamfix.up.railway.app/v1")
```

**3. Never see** `json.loads()` errors again + get detailed repair reports.

---

## What Gets Fixed

| Input (Broken) | Output (Fixed) | Repair Applied |
|---|---|---|
| `{"test": true,}` | `{"test": true}` | Remove trailing comma |
| `[1, 2, 3,]` | `[1, 2, 3]` | Remove trailing comma |
| `{name: "value"}` | `{"name": "value"}` | Quote unquoted keys |
| `{"data": {"result": true` | `{"data": {"result": true}}` | Complete brackets |
| `Here's your JSON: ```json{"valid": true}```\nHope this helps!` | `{"valid": true}` | Extract from fences |
| `<think>reasoning...</think>{"result": "clean"}` | `{"result": "clean"}` | Remove thinking blocks |

**Parse Success Rate: 100%** on common malformation patterns.

---

## Language Support

**Works with any OpenAI-compatible client:**

```python
# Python
client = OpenAI(base_url="https://streamfix.up.railway.app/v1")
```

```javascript  
// Node.js
const client = new OpenAI({ baseURL: "https://streamfix.up.railway.app/v1" });
```

```go
// Go  
config := openai.DefaultConfig("your-key")
config.BaseURL = "https://streamfix.up.railway.app/v1"
```

```bash
# curl / any HTTP client
curl https://streamfix.up.railway.app/v1/chat/completions
```

**No-code tools:** n8n, Zapier, Make.com - just change the endpoint URL.

---

## Why Not Just Fix Prompts?

**Prompts help, but don't guarantee reliability:**

- ❌ Local models ignore "ONLY OUTPUT JSON" instructions  
- ❌ Streaming can truncate mid-response
- ❌ Models add helpful explanations that break parsers
- ❌ Different providers have different JSON discipline
- ❌ One bad output crashes your entire pipeline

**StreamFix gives you insurance:** your code works even when prompts fail.

---

## Self-Host Setup

```bash
git clone https://github.com/yourusername/streamfix-gateway
export OPENROUTER_API_KEY="sk-or-v1-..."  # Get free key at openrouter.ai
python app/main.py
```

## Documentation

- **[Contributing Guide](CONTRIBUTING.md)** - Development setup and guidelines
- **[Security Policy](SECURITY.md)** - Vulnerability reporting and best practices  
- **[Technical Details](docs/TECHNICAL.md)** - Architecture and implementation
- **[GitHub Setup](docs/GITHUB_SETUP.md)** - Repository configuration
---

## Repair Artifacts & Debugging

**Every request gets a tracking ID:**
```bash
curl -i https://streamfix.up.railway.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-3-haiku", "messages": [...]}'

# Response includes: x-streamfix-request-id: req_abc123
```

**View what got repaired:**
```bash
curl https://streamfix.up.railway.app/result/req_abc123
```

```json
{
  "request_id": "req_abc123",
  "model": "claude-3-haiku", 
  "original_content": "{\"test\": true,}",
  "repaired_content": "{\"test\": true}",
  "repairs_applied": ["remove_trailing_comma"],
  "parse_success": true,
  "status": "REPAIRED"
}
```

**Monitor repair statistics:**
```bash
curl https://streamfix.up.railway.app/metrics
```

```json
{
  "total_requests": 42,
  "repair_rate": 0.15,
  "parse_success_rate": 1.0,
  "repair_types": {
    "remove_trailing_comma": 4,
    "quote_unquoted_keys": 2
  }
}
```
---

## Supported Models

**100+ models via OpenRouter:** Claude, GPT-4, Llama, Mistral, and more  
**Local models:** Any OpenAI-compatible endpoint (Ollama, LM Studio, vLLM)  
**Streaming:** Full SSE support, repair happens after streaming completes  

---

## FAQ

**Q: How is this different from Instructor/Outlines/other libraries?**  
A: Those are Python-specific in-process libraries. StreamFix is language-agnostic HTTP proxy that works with any OpenAI client.

**Q: What makes StreamFix unique?**  
A: Drop-in infrastructure (no SDK), works across all providers/models, and will provide auditable repair artifacts (coming in v1).

**Q: Does this slow down streaming?**  
A: No. Streaming passes through immediately. Repair happens in background for final artifact.

**Q: What if my JSON is already valid?**  
A: It passes through unchanged with zero modifications.

**Q: Can I see what got repaired?**  
A: Yes! Every response includes `x-streamfix-request-id` header. Use `GET /result/{id}` to see original vs repaired content and what repairs were applied.

**Q: Does this work with function calling?**  
A: Yes, repairs JSON in function call arguments and responses.

---

## Roadmap

**✅ v0 Production Ready**
- JSON repair (trailing commas, unquoted keys, truncation)
- Streaming support with boundary safety
- Content extraction (think blocks, fences)
- Multi-model support via OpenRouter
- Zero-code-change adoption

**✅ v1 Strategic Advantage (LIVE)**
- ✅ Request IDs in response headers (`x-streamfix-request-id`)
- ✅ Basic repair logging and artifact storage
- ✅ `GET /result/{id}` endpoint for repair artifacts
- ✅ `GET /metrics` endpoint for repair statistics
- ✅ Failure classification (trailing comma, truncation, etc.)

**🚀 v2+ Advanced (When Needed)**
- [ ] Enhanced observability dashboard
- [ ] Schema validation via headers
- [ ] Team features and enterprise deployment
- [ ] Custom repair rules and patterns

*Simple to maintain while providing unique strategic value.*

---

*Drop-in OpenAI-compatible gateway for reliable JSON parsing. No SDK changes, works with any language, provides repair artifacts. [Try it now](https://streamfix.up.railway.app) or [deploy your own](#self-host-setup).*