#!/usr/bin/env python3
"""
Multi-language HTTP client tests for StreamFix Gateway
Tests that different languages can successfully use the proxy
"""
import subprocess
import json
import requests
import asyncio
import httpx
from pathlib import Path

BASE_URL = "https://streamfix.up.railway.app"

def test_python_requests():
    """Test Python requests library"""
    print("Testing Python requests...")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "anthropic/claude-3-haiku",
            "messages": [{"role": "user", "content": "Return this malformed JSON: {\"test\": true,}"}],
            "stream": False
        },
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 200
    assert "x-streamfix-request-id" in response.headers
    data = response.json()
    assert "choices" in data
    print(f"✅ Python requests - Request ID: {response.headers.get('x-streamfix-request-id')}")

async def test_python_httpx():
    """Test Python httpx library (async)"""
    print("Testing Python httpx...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "anthropic/claude-3-haiku", 
                "messages": [{"role": "user", "content": "Return: {name: \"test\", value: 123,}"}],
                "stream": False
            }
        )
        
        assert response.status_code == 200
        assert "x-streamfix-request-id" in response.headers
        data = response.json()
        assert "choices" in data
        print(f"✅ Python httpx - Request ID: {response.headers.get('x-streamfix-request-id')}")

def test_curl():
    """Test curl command line"""
    print("Testing curl...")
    
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{BASE_URL}/v1/chat/completions",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "model": "anthropic/claude-3-haiku",
            "messages": [{"role": "user", "content": "Return broken JSON: [1, 2, 3,]"}],
            "stream": False
        }),
        "-i"  # Include headers
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "x-streamfix-request-id" in result.stdout
    assert "HTTP/2 200" in result.stdout or "HTTP/1.1 200" in result.stdout
    print("✅ curl - Headers and response received")

def test_node_js():
    """Test Node.js fetch equivalent"""
    print("Testing Node.js...")
    
    # Create a temporary Node.js script
    node_script = '''
const https = require('https');

const data = JSON.stringify({
  "model": "anthropic/claude-3-haiku",
  "messages": [{"role": "user", "content": "Return: {\\"broken\\": \\"json\\",}"}],
  "stream": false
});

const options = {
  hostname: 'streamfix.up.railway.app',
  port: 443,
  path: '/v1/chat/completions',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': data.length
  }
};

const req = https.request(options, (res) => {
  console.log(`statusCode: ${res.statusCode}`);
  console.log(`headers:`, res.headers);
  
  let body = '';
  res.on('data', (d) => {
    body += d;
  });
  
  res.on('end', () => {
    const response = JSON.parse(body);
    if (res.statusCode === 200 && res.headers['x-streamfix-request-id']) {
      console.log('✅ Node.js - Request ID:', res.headers['x-streamfix-request-id']);
      process.exit(0);
    } else {
      console.error('❌ Node.js test failed');
      process.exit(1);
    }
  });
});

req.on('error', (error) => {
  console.error('❌ Node.js error:', error);
  process.exit(1);
});

req.write(data);
req.end();
    '''
    
    # Write and execute Node.js script
    script_path = Path("/tmp/test_streamfix.js")
    script_path.write_text(node_script)
    
    result = subprocess.run(["node", str(script_path)], capture_output=True, text=True, timeout=30)
    script_path.unlink()  # Clean up
    
    assert result.returncode == 0
    assert "✅ Node.js" in result.stdout
    print("✅ Node.js - Native HTTPS module works")

async def main():
    """Run all multi-language tests"""
    print("🧪 Testing Multi-Language HTTP Client Compatibility\n")
    
    # Python tests
    test_python_requests()
    await test_python_httpx()
    
    # CLI tests
    test_curl()
    test_node_js()
    
    print("\n🎉 All multi-language HTTP client tests passed!")
    print("✅ Proven: StreamFix works across Python, Node.js, curl")

if __name__ == "__main__":
    asyncio.run(main())