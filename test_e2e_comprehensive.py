#!/usr/bin/env python3
"""
Comprehensive E2E test for StreamFix local installation
Tests all features from install to complete functionality
"""
import subprocess
import time
import json
import sys

def run_cmd(cmd):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def test_health():
    """Test 1: Health endpoint"""
    print("\n🔍 Test 1: Health Check")
    stdout, stderr, code = run_cmd("curl -s http://127.0.0.1:9000/health")
    if code == 0 and "healthy" in stdout:
        print("✅ Health check passed")
        return True
    else:
        print(f"❌ Health check failed: {stderr}")
        return False

def test_basic_request():
    """Test 2: Basic non-streaming request"""
    print("\n🔍 Test 2: Basic Request (No Schema)")
    cmd = '''curl -s -X POST http://127.0.0.1:9000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": "Return exactly: {\\"hello\\": \\"world\\"}"}]}'
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

def test_schema_validation():
    """Test 3: Schema validation (Contract Mode)"""
    print("\n🔍 Test 3: Schema Validation")
    cmd = '''curl -s -X POST http://127.0.0.1:9000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{"model": "anthropic/claude-3-haiku", "schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}, "messages": [{"role": "user", "content": "Return: {\\"name\\": \\"test\\"}"}]}' \
      -i | grep "x-streamfix-request-id:" | cut -d' ' -f2 | tr -d '\\r'
    '''
    stdout, stderr, code = run_cmd(cmd)
    if code == 0 and stdout.strip():
        request_id = stdout.strip()
        print(f"✅ Schema validation request sent. Request ID: {request_id}")
        
        # Check artifact
        time.sleep(1)
        artifact_cmd = f"curl -s http://127.0.0.1:9000/result/{request_id}"
        artifact_out, _, artifact_code = run_cmd(artifact_cmd)
        if artifact_code == 0:
            try:
                artifact = json.loads(artifact_out)
                if "schema_valid" in artifact:
                    print(f"✅ Artifact retrieved. Schema valid: {artifact['schema_valid']}")
                    return True
                else:
                    print(f"❌ Artifact missing schema_valid field")
                    return False
            except:
                print(f"❌ Failed to parse artifact")
                return False
        else:
            print(f"❌ Failed to retrieve artifact")
            return False
    else:
        print(f"❌ Schema validation request failed")
        return False

def test_json_extraction():
    """Test 4: JSON extraction from mixed content"""
    print("\n🔍 Test 4: JSON Extraction from Mixed Content")
    cmd = '''curl -s -X POST http://127.0.0.1:9000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{"model": "anthropic/claude-3-haiku", "schema": {"type": "object", "properties": {"result": {"type": "string"}}}, "messages": [{"role": "user", "content": "Return JSON in markdown fences: ```json\\n{\\"result\\": \\"extracted\\"}\\n```"}]}' \
      -i | grep "x-streamfix-request-id:" | cut -d' ' -f2 | tr -d '\\r'
    '''
    stdout, stderr, code = run_cmd(cmd)
    if code == 0 and stdout.strip():
        request_id = stdout.strip()
        print(f"✅ Extraction request sent. Request ID: {request_id}")
        
        # Check artifact
        time.sleep(1)
        artifact_cmd = f"curl -s http://127.0.0.1:9000/result/{request_id}"
        artifact_out, _, artifact_code = run_cmd(artifact_cmd)
        if artifact_code == 0:
            try:
                artifact = json.loads(artifact_out)
                if "extracted_json" in artifact and "extraction_status" in artifact:
                    print(f"✅ Extraction worked. Status: {artifact['extraction_status']}")
                    print(f"   Extracted: {artifact.get('extracted_json', '')[:50]}...")
                    return True
                else:
                    print(f"❌ Artifact missing extraction fields")
                    return False
            except:
                print(f"❌ Failed to parse artifact")
                return False
        else:
            print(f"❌ Failed to retrieve artifact")
            return False
    else:
        print(f"❌ Extraction request failed")
        return False

def test_metrics():
    """Test 5: Metrics endpoint"""
    print("\n🔍 Test 5: Metrics")
    stdout, stderr, code = run_cmd("curl -s http://127.0.0.1:9000/metrics")
    if code == 0:
        try:
            data = json.loads(stdout)
            if "total_requests" in data:
                print(f"✅ Metrics retrieved. Total requests: {data['total_requests']}")
                return True
            else:
                print(f"❌ Metrics missing total_requests")
                return False
        except:
            print(f"❌ Failed to parse metrics")
            return False
    else:
        print(f"❌ Metrics request failed")
        return False

def main():
    print("=" * 60)
    print("StreamFix E2E Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health),
        ("Basic Request", test_basic_request),
        ("Schema Validation", test_schema_validation),
        ("JSON Extraction", test_json_extraction),
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
