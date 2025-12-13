# StreamFix Gateway

> **Stop building retry loops. `json.loads()` always works.**

[![Production](https://img.shields.io/badge/status-production_ready-green.svg)](https://streamfix.up.railway.app)
[![Parse Success](https://img.shields.io/badge/parse_success-100%25-brightgreen.svg)](#)
[![Models](https://img.shields.io/badge/models-100%2B_supported-blue.svg)](#)

**🌐 Try it now:** `https://streamfix.up.railway.app/v1/chat/completions`

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
  }'
```

**2. Point your existing code** at StreamFix:
```python
# Before: unreliable parsing
client = OpenAI()

# After: guaranteed parsing  
client = OpenAI(base_url="https://streamfix.up.railway.app/v1")
```

**3. Never see** `json.loads()` errors again.

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

Deploy anywhere: Railway, Fly.io, AWS, your laptop.

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
A: Working on repair reports - will show original vs repaired JSON with applied fixes.

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

**🎯 v1 Strategic Advantage (Simple)**
- [ ] Request IDs in response headers (`x-streamfix-request-id`)
- [ ] Basic repair logging (what got fixed)
- [ ] Simple `/result/{id}` endpoint for repair artifacts
- [ ] Failure classification (trailing comma, truncation, etc.)

**🚀 v2+ Advanced (When Needed)**
- [ ] Usage analytics and model reliability rankings
- [ ] Schema validation via headers
- [ ] Team features and observability dashboard

*Keeping it simple to maintain while providing unique value.*

---

*Drop-in OpenAI-compatible gateway for reliable JSON parsing. No SDK changes, works with any language, provides repair artifacts. [Try it now](https://streamfix.up.railway.app) or [deploy your own](#self-host-setup).*