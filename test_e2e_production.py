#!/usr/bin/env python3
"""
E2E test against production deployment
Tests all features work end-to-end
"""
import subprocess
import time
import json
import sys

ENDPOINT = "https://streamfix.up.railway.app"

def run_cmd(cmd):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def test_health():
    """Test 1: Health endpoint"""
    print("\n🔍 Test 1: Health Check")
    stdout, stderr, code = run_cmd(f"curl -s {ENDPOINT}/health")
    if code == 0 and "healthy" in stdout:
        print("✅ Health check passed")
        return True
    else:
        print(f"❌ Health check failed: {stderr}")
        return False

def test_basic_request():
    """Test 2: Basic non-streaming request"""
    print("\n🔍 Test 2: Basic Request")
    cmd = f'''curl -s -X POST {ENDPOINT}/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{{"model": "anthropic/claude-3-haiku", "messages": [{{"role": "user", "content": "Say: hello"}}]}}'
    '''
    stdout, stderr, code = run_cmd(cmd)
    if code == 0:
        try:
            data = json.loads(stdout)
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ Basic request passed. Response: {content[:50]}...")
            return True
        except Exception as e:
            print(f"❌ Failed to parse response: {e}")
            return False
    else:
        print(f"❌ Request failed: {stderr}")
        return False

def test_contract_mode():
    """Test 3: Contract Mode with Phase 2 features"""
    print("\n🔍 Test 3: Contract Mode (Phase 2)")
    cmd = f'''curl -s -X POST {ENDPOINT}/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{{"model": "anthropic/claude-3-haiku", "schema": {{"type": "object", "properties": {{"status": {{"type": "string"}}}}, "required": ["status"]}}, "messages": [{{"role": "user", "content": "Return: {{\\\"status\\\": \\\"ok\\\"}}"}}]}}' \
      -i | grep "x-streamfix-request-id:" | cut -d' ' -f2 | tr -d '\\r'
    '''
    stdout, stderr, code = run_cmd(cmd)
    if code == 0 and stdout.strip():
        request_id = stdout.strip()
        print(f"✅ Contract Mode request sent. Request ID: {request_id}")
        
        # Check artifact
        time.sleep(2)
        artifact_cmd = f"curl -s {ENDPOINT}/result/{request_id}"
        artifact_out, _, artifact_code = run_cmd(artifact_cmd)
        if artifact_code == 0:
            try:
                artifact = json.loads(artifact_out)
                has_phase2 = all(k in artifact for k in ["extracted_json", "extraction_status", "schema_valid"])
                if has_phase2:
                    print(f"✅ Phase 2 features present:")
                    print(f"   - Extraction status: {artifact['extraction_status']}")
                    print(f"   - Schema valid: {artifact['schema_valid']}")
                    print(f"   - Extracted: {artifact.get('extracted_json', '')[:40]}...")
                    return True
                else:
                    print(f"❌ Missing Phase 2 fields in artifact")
                    return False
            except Exception as e:
                print(f"❌ Failed to parse artifact: {e}")
                return False
        else:
            print(f"❌ Failed to retrieve artifact")
            return False
    else:
        print(f"❌ Contract Mode request failed")
        return False

def test_schema_violation():
    """Test 4: Schema validation error messages"""
    print("\n🔍 Test 4: Schema Violation Detection")
    cmd = f'''curl -s -X POST {ENDPOINT}/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{{"model": "anthropic/claude-3-haiku", "schema": {{"type": "object", "properties": {{"name": {{"type": "string"}}, "age": {{"type": "integer"}}}}, "required": ["name", "age"]}}, "messages": [{{"role": "user", "content": "Return: {{\\\"name\\\": \\\"test\\\"}}"}}]}}' \
      -i | grep "x-streamfix-request-id:" | cut -d' ' -f2 | tr -d '\\r'
    '''
    stdout, stderr, code = run_cmd(cmd)
    if code == 0 and stdout.strip():
        request_id = stdout.strip()
        print(f"✅ Schema violation test sent. Request ID: {request_id}")
        
        # Check artifact
        time.sleep(2)
        artifact_cmd = f"curl -s {ENDPOINT}/result/{request_id}"
        artifact_out, _, artifact_code = run_cmd(artifact_cmd)
        if artifact_code == 0:
            try:
                artifact = json.loads(artifact_out)
                if artifact.get("status") == "SCHEMA_INVALID" and artifact.get("schema_errors"):
                    print(f"✅ Schema violation detected correctly")
                    print(f"   Errors: {artifact['schema_errors'][0][:60]}...")
                    return True
                else:
                    print(f"❌ Schema violation not detected properly")
                    return False
            except Exception as e:
                print(f"❌ Failed to parse artifact: {e}")
                return False
        else:
            print(f"❌ Failed to retrieve artifact")
            return False
    else:
        print(f"❌ Schema violation test failed")
        return False

def test_metrics():
    """Test 5: Metrics endpoint"""
    print("\n🔍 Test 5: Metrics")
    stdout, stderr, code = run_cmd(f"curl -s {ENDPOINT}/metrics")
    if code == 0:
        try:
            data = json.loads(stdout)
            if "total_requests" in data or "message" in data:
                print(f"✅ Metrics endpoint working")
                if "total_requests" in data:
                    print(f"   Total requests: {data['total_requests']}")
                return True
            else:
                print(f"❌ Unexpected metrics format")
                return False
        except Exception as e:
            print(f"❌ Failed to parse metrics: {e}")
            return False
    else:
        print(f"❌ Metrics request failed")
        return False

def main():
    print("=" * 60)
    print("StreamFix E2E Production Test Suite")
    print("=" * 60)
    print(f"Testing against: {ENDPOINT}")
    print()
    
    tests = [
        ("Health Check", test_health),
        ("Basic Request", test_basic_request),
        ("Contract Mode (Phase 2)", test_contract_mode),
        ("Schema Violation Detection", test_schema_violation),
        ("Metrics", test_metrics),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! StreamFix is fully functional.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
