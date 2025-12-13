# StreamFix Gateway 🔧

> Make any AI API return reliable JSON - fix trailing commas, complete truncated responses, and extract clean data automatically.

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 **Why StreamFix?**

AI models frequently generate malformed JSON that breaks applications:

```json
❌ {"status": "success", "items": [1,2,3,],}  // Trailing comma
❌ {"data": {"result": true               // Truncated
❌ Here's your JSON: ```json{"valid": true}``` // Mixed content
```

StreamFix automatically repairs these issues in real-time:

```json
✅ {"status": "success", "items": [1,2,3]}
✅ {"data": {"result": true}}
✅ {"valid": true}
```

## ✨ **Features**

- 🔧 **Automatic JSON Repair** - Fixes trailing commas, completes truncated structures
- ⚡ **Real-time Streaming** - Processes Server-Sent Events (SSE) as they arrive
- 🎯 **Smart Content Extraction** - Removes thinking blocks, extracts from code fences
- 🔗 **Drop-in Replacement** - OpenAI-compatible API, works with existing code
- 🧠 **FSM-Powered** - Finite State Machine handles any malformation automatically
- 🆓 **Completely Free** - No usage limits, no tracking, just reliable JSON

## 🏃‍♂️ **Quick Start**

### **Self-Hosted Setup**

**1. Clone & Install:**
```bash
git clone https://github.com/yourusername/streamfix-gateway
cd streamfix-gateway
pip install -r requirements.txt
```

**3. Configure Environment:**
```bash
cp .env.example .env
# Add your OpenRouter API key to .env
```

**3. Run:**
```bash
# Development
python -m uvicorn app.main:app --reload

# Production  
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**4. Test:**
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4", 
    "stream": true,
    "messages": [{"role": "user", "content": "Return JSON with trailing commas"}]
  }'
```

## 📖 **Usage Examples**

### **Before StreamFix:**
```python
import openai

response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Return a JSON config"}]
)

content = response.choices[0].message.content
# Often fails: json.loads(content) ❌ 
```

### **After StreamFix:**
```python
import openai

# Just change the base_url
client = openai.OpenAI(base_url="http://localhost:8000/v1")

response = client.chat.completions.create(
    model="gpt-4", 
    messages=[{"role": "user", "content": "Return a JSON config"}]
)

content = response.choices[0].message.content
data = json.loads(content)  # Always works ✅
```

## 🚀 **Deploy to Railway**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/yourusername/streamfix-gateway)

Environment Variables:
```
OPENROUTER_API_KEY=your_key
PORT=8000
```

## 🧪 **Testing**

```bash
# Test core engine
python scripts/smoke_engine.py

# Full validation  
python scripts/day1_validation.py
```

## 📄 **License**

MIT License - see LICENSE file for details.