# StreamFix 🔧 
### Free & Open Source JSON Repair Gateway

**Make any AI API return reliable JSON automatically**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/your-username/streamfix)
[![Docker Hub](https://img.shields.io/docker/v/streamfix/gateway.svg)](https://hub.docker.com/r/streamfix/gateway)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 **The Problem**

AI models constantly break your apps with malformed JSON:

```json
❌ {"status": "ok", "data": [1,2,3,],}     // Trailing comma
❌ {"message": "Here's some JSON: ```json{"key": "value"}```"}  // Code fence
❌ {"response": {"text": true              // Truncated response  
❌ {"key": 'single quotes'}                // Wrong quote types
```

**Result**: `json.loads()` crashes and your users see errors.

## ✨ **The Solution**

StreamFix sits between your app and any AI API, automatically repairing JSON in real-time:

```json
✅ {"status": "ok", "data": [1,2,3]}
✅ {"key": "value"}  
✅ {"response": {"text": true}}
✅ {"key": "single quotes"}
```

**Result**: `json.loads()` always works. Your app never breaks.

---

## 🚀 **Get Started in 30 Seconds**

### Option 1: Use Our Free Hosted Version
```python
import openai

# Just change the base_url - everything else stays the same
client = openai.OpenAI(
    base_url="https://streamfix.up.railway.app/v1",
    api_key="your-openrouter-key"
)

response = client.chat.completions.create(
    model="openai/gpt-4",
    messages=[{"role": "user", "content": "Return JSON config"}]
)

# This will ALWAYS work - no more JSON parsing errors!
data = json.loads(response.choices[0].message.content)
```

### Option 2: Self-Host (One Command)
```bash
git clone https://github.com/your-username/streamfix
cd streamfix
echo "OPENROUTER_API_KEY=your_key_here" > .env
docker compose up
```

That's it! Your StreamFix gateway is running on `http://localhost:8000`

---

## 🔧 **How It Works**

1. **Drop-in Replacement**: Compatible with OpenAI API - just change the `base_url`
2. **Real-time Repair**: Fixes JSON as it streams from AI models
3. **Smart Extraction**: Removes thinking blocks, extracts from code fences  
4. **Zero Breaking Changes**: Your existing code works unchanged

### Supported Repairs

- ✅ **Trailing commas**: `{"key": "value",}` → `{"key": "value"}`
- ✅ **Truncated JSON**: `{"partial": true` → `{"partial": true}`
- ✅ **Code fence extraction**: ` ```json{"data": 1}``` ` → `{"data": 1}`
- ✅ **Mixed content**: `Here's JSON: {"valid": true}` → `{"valid": true}`
- ✅ **Single quotes**: `{'key': 'value'}` → `{"key": "value"}`
- ✅ **Unescaped quotes**: `{"text": "say "hi""}` → `{"text": "say \"hi\""}`

---

## 💡 **Why Free & Open Source?**

We believe reliable JSON should be a solved problem, not a paid service. StreamFix is:

- **🆓 Completely Free**: No usage limits, no credit cards, no gotchas
- **🔓 Fully Open Source**: MIT license, contribute and modify freely  
- **🏠 Self-Hostable**: Run on your infrastructure with full control
- **🌍 Community-Driven**: Built by developers, for developers

**Our Philosophy**: Start free, build community. If people love it, we might add premium features later (advanced monitoring, enterprise support, etc.) while keeping the core JSON repair completely free forever.

---

## ⚙️ **Configuration**

### Environment Variables
```bash
OPENROUTER_API_KEY=your_api_key_here  # Required for hosted version
PORT=8000                            # Optional: Server port (default: 8000)
```

### Docker Compose
```yaml
version: '3.8'
services:
  streamfix:
    image: streamfix/gateway:latest
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
```

---

## 📚 **Examples**

### Before StreamFix (Brittle)
```python
import openai
import json

client = openai.OpenAI(api_key="your-key")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Return a JSON config"}]
)

# This often fails with JSON parse errors
try:
    data = json.loads(response.choices[0].message.content)
except json.JSONDecodeError as e:
    print(f"JSON Error: {e}")  # 😞 Happens constantly
```

### After StreamFix (Bulletproof)
```python
import openai
import json

# Just change the base_url - everything else identical
client = openai.OpenAI(
    base_url="https://streamfix.up.railway.app/v1",
    api_key="your-openrouter-key"
)

response = client.chat.completions.create(
    model="openai/gpt-4", 
    messages=[{"role": "user", "content": "Return a JSON config"}]
)

# This ALWAYS works - StreamFix repairs JSON automatically
data = json.loads(response.choices[0].message.content)  # 🎉 Never fails
print(data)  # Perfect JSON every time
```

### Streaming Support
```python
# Streaming works exactly the same way
stream = client.chat.completions.create(
    model="openai/gpt-4",
    messages=[{"role": "user", "content": "Stream a JSON response"}],
    stream=True
)

content = ""
for chunk in stream:
    if chunk.choices[0].delta.content:
        content += chunk.choices[0].delta.content

# StreamFix repairs the JSON even in streaming mode
data = json.loads(content)  # Always perfect
```

---

## 🧪 **Testing**

```bash
# Test the core engine locally
python -c "
from app.core.repair import safe_repair
test_json = '{\"broken\": \"json\",}'
fixed = safe_repair(test_json)
print('Fixed:', fixed)
"

# Test the full gateway
curl http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "openai/gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Return broken JSON with trailing commas"}],
    "stream": false
  }'
```

---

## 🤝 **Contributing**

We welcome all contributions! StreamFix is built with:

- **FastAPI**: Modern, fast web framework
- **Python 3.12+**: Latest Python features  
- **Finite State Machine**: Robust JSON parsing and repair
- **OpenAI Compatible**: Drop-in replacement for OpenAI API

### Quick Development Setup
```bash
git clone https://github.com/your-username/streamfix
cd streamfix
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Run locally
python -m uvicorn app.main:app --reload
```

### Project Structure
```
streamfix/
├── app/
│   ├── core/           # JSON repair engine & FSM
│   ├── api/           # FastAPI routes  
│   └── main.py        # Application entry point
├── tests/             # Test suite
├── docker/           # Docker configuration
└── docs/             # Documentation
```

---

## 🎉 **What's Next?**

StreamFix v1 is focused on one thing: **making JSON repair invisible and reliable**.

**Potential future features** (if the community wants them):
- Advanced repair analytics and monitoring
- Custom repair rules and configurations  
- Enterprise SSO and team management
- Dedicated hosted instances for high-volume users
- Premium support and SLAs

But the core JSON repair will always be free and open source.

---

## 📄 **License**

MIT License - see [LICENSE](LICENSE) for full details.

**TL;DR**: Use it for anything, commercial or personal, with zero restrictions.

---

## ❤️ **Support**

- **⭐ Star the repo** if StreamFix saves you debugging time
- **🐛 Report issues** at [GitHub Issues](https://github.com/your-username/streamfix/issues)  
- **💡 Suggest features** via [Discussions](https://github.com/your-username/streamfix/discussions)
- **🔀 Submit PRs** to make it better for everyone

---

**Made with ❤️ by developers tired of broken JSON**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/your-username/streamfix)