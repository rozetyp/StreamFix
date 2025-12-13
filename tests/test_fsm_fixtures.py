import pytest
from pathlib import Path
from app.core.fsm import PreprocessState, JsonFsmState, preprocess_chunk, preprocess_complete, preprocess_finalize, preprocess_get_result, preprocess_streaming, fsm_feed, fsm_result, fsm_finalize
from app.core.repair import safe_repair, attempt_json_parse

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> str:
    """Load a test fixture file"""
    return (FIXTURES_DIR / filename).read_text().strip()


def simulate_streaming_chunks(text: str, chunk_size: int = 8) -> list[str]:
    """Simulate streaming by breaking text into chunks"""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks


class TestPreprocessor:
    """Test the streaming preprocessor"""
    
    def test_simple_fenced_json(self):
        content = load_fixture("01_simple_fenced.txt")
        
        result = preprocess_complete(content)
        
        # Should extract just the JSON
        assert result.strip() == '{"name": "John", "age": 30}'
    
    def test_think_block_removal(self):
        content = load_fixture("02_think_block.txt") 
        
        result = preprocess_complete(content)
        
        # Should remove <think> block and keep JSON
        assert '"result": "success"' in result
        assert '<think>' not in result
        assert '</think>' not in result
    
    def test_mixed_content_with_fences(self):
        content = load_fixture("06_mixed_content.txt")
        
        result = preprocess_complete(content)
        
        # Should extract only the fenced JSON
        expected = '{"response": "clean", "status": "success"}'
        assert result.strip() == expected
    
    def test_close_think_tag_boundary_split(self):
        """Test </think> close tag split across boundaries"""
        # Create content where close think tag is split but still valid
        content = "# Test fixture: Close think tag split\n<think>\nReasoning content\n</think>\n\n{\"boundary\": \"test6\"}"
        
        # Test the invariant
        complete_result = preprocess_complete(content)
        
        # Split at: "</thi|nk>"
        split_pos = content.find('</thi') + 5  # Split after "</thi"
        chunks = [content[:split_pos], content[split_pos:]]
        streaming_result = preprocess_streaming(chunks)
        
        # Core invariant
        assert streaming_result == complete_result
        assert '<think>' not in streaming_result
        assert '</think>' not in streaming_result
        assert '"boundary": "test6"' in streaming_result
    
    def test_fence_language_boundary_split(self):
        """Test fence language line split across boundaries"""
        # Create content where fence language line is split
        content = "# Test fixture: Fence language split\n```ja\nvascript\n{\"boundary\": \"test7\"}\n```"
        
        # Test the invariant
        complete_result = preprocess_complete(content)
        
        # Split in fence language: "```ja|vascript"
        split_pos = content.find('```ja') + 5  # Split after "```ja"
        chunks = [content[:split_pos], content[split_pos:]]
        streaming_result = preprocess_streaming(chunks)
        
        # Core invariant - should extract fence content
        assert streaming_result == complete_result
        # The fence should extract content after language line
        assert '{\"boundary\": \"test7\"}' in streaming_result

    def test_randomized_chunk_boundaries(self):
        """Property test: streaming with random boundaries equals complete processing"""
        content = load_fixture("08_deepseek_reasoning.txt")
        complete_result = preprocess_complete(content)
        
        import random
        
        # Test 10 random chunkings
        for seed in range(10):
            random.seed(seed)
            # Generate random split positions
            splits = sorted(random.sample(range(1, len(content)), k=random.randint(1, 5)))
            
            chunks = []
            start = 0
            for split in splits:
                chunks.append(content[start:split])
                start = split
            chunks.append(content[start:])  # Final chunk
            
            streaming_result = preprocess_streaming(chunks)
            assert streaming_result == complete_result, f"Failed with seed {seed}, splits {splits}"
        content = load_fixture("10_multiple_thinks.txt")
        
        result = preprocess_complete(content)
        
        # Should remove all think blocks
        assert '<think>' not in result
        assert '"analysis": "complete"' in result
    
    def test_extraction_invariant(self):
        """Test extraction invariant: extract_json(preprocess_complete(text)) == extract_json_stream(preprocess_chunk(...)+finalize)"""
        content = load_fixture("08_deepseek_reasoning.txt")
        
        # Method 1: Complete processing
        complete_preprocessed = preprocess_complete(content)
        fsm1 = JsonFsmState()
        fsm_feed(fsm1, complete_preprocessed) 
        fsm_finalize(fsm1)
        result1, status1 = fsm_result(fsm1)
        
        # Method 2: Streaming processing
        preprocess_state = PreprocessState()
        cleaned = preprocess_chunk(content, preprocess_state)
        tail = preprocess_finalize(preprocess_state)
        
        fsm2 = JsonFsmState()
        fsm_feed(fsm2, cleaned + tail)
        fsm_finalize(fsm2)
        result2, status2 = fsm_result(fsm2)
        
        # Core invariant
        assert result1 == result2, f"Extraction results differ: {repr(result1)} != {repr(result2)}"
        assert status1 == status2, f"Extraction status differs: {status1} != {status2}"

    def test_streaming_chunks(self):
        """Test that preprocessing works correctly across chunks"""
        content = load_fixture("08_deepseek_reasoning.txt")
        state = PreprocessState()

        chunks = simulate_streaming_chunks(content, chunk_size=15)
        result_parts = []

        for chunk in chunks:
            part = preprocess_chunk(chunk, state)
            result_parts.append(part)

        result = "".join(result_parts)

        # Should work the same as processing all at once
        assert '<think>' not in result
        assert '"languages"' in result
    
    def test_think_tag_boundary_split(self):
        """Test think tag split across chunk boundaries"""
        # Use content where think tag spans the boundary
        content = "# Test fixture: Think tag split across chunks\n<think>\nSome reasoning here\n</think>\n\n{\"boundary\": \"test1\"}"
        
        # Test the invariant: streaming == complete processing
        complete_result = preprocess_complete(content)
        
        # Split at the boundary: "<thi|nk>"
        split_pos = content.find('<think>') + 4  # Split after "<thi"
        chunks = [content[:split_pos], content[split_pos:]]
        streaming_result = preprocess_streaming(chunks)
        
        # Core invariant
        assert streaming_result == complete_result
        assert '<think>' not in streaming_result
        assert '</think>' not in streaming_result
        assert '"boundary": "test1"' in streaming_result
    
    def test_fence_tag_boundary_split(self):
        """Test fence tag split across chunk boundaries"""
        # Create a proper fixture programmatically
        content = "# Test fixture: Fence tag split across chunks\n```json\n{\"boundary\": \"test2\"}\n```"
        
        # Test the invariant: streaming == complete processing
        complete_result = preprocess_complete(content)
        
        # Split at the boundary: "``|`json"
        split_pos = content.find('```') + 2  # Split after "``"
        chunks = [content[:split_pos], content[split_pos:]]
        streaming_result = preprocess_streaming(chunks)
        
        # Core invariant
        assert streaming_result == complete_result
        assert streaming_result.strip() == '{"boundary": "test2"}'
    
    def test_close_fence_boundary_split(self):
        """Test close fence tag split across boundaries"""
        # Create proper fixture programmatically
        content = "# Test fixture: Close fence split\n```json\n{\"boundary\": \"test4\"}\n```"
        
        # Test the invariant: streaming == complete processing
        complete_result = preprocess_complete(content)
        
        # Split at close fence: "``|`"
        close_pos = content.rfind('```') + 2  # Split at last fence, after "``"
        chunks = [content[:close_pos], content[close_pos:]]
        streaming_result = preprocess_streaming(chunks)
        
        # Core invariant
        assert streaming_result == complete_result
        assert streaming_result.strip() == '{"boundary": "test4"}'
    
    def test_json_content_boundary_split(self):
        """Test JSON content split across boundaries"""
        # Create proper fixture programmatically
        content = "# Test fixture: JSON split across chunks\n<think>\nSome reasoning here\n</think>\n\n{\"boundary\": \"test5\"}"
        
        # Test the invariant: streaming == complete processing
        complete_result = preprocess_complete(content)
        
        # Split JSON in middle of value
        json_start = content.find('"boundary"')
        split_pos = json_start + 12  # Split in middle of "test5"
        chunks = [content[:split_pos], content[split_pos:]]
        streaming_result = preprocess_streaming(chunks)
        
        # Core invariant
        assert streaming_result == complete_result
        assert '<think>' not in streaming_result
        assert '"boundary": "test5"' in streaming_result
    
    def test_close_think_tag_boundary_split(self):
        """Test </think> close tag split across boundaries"""
        # Create content where close think tag is split but valid when reconstructed
        content = "# Test fixture: Close think tag split\n<think>\nReasoning content\n</think>\n\n{\"boundary\": \"test6\"}"
        
        # Test the invariant: streaming == complete processing
        complete_result = preprocess_complete(content)
        
        # Split at: "</thi|nk>"
        split_pos = content.find('</thi') + 5  # Split after "</thi"
        chunks = [content[:split_pos], content[split_pos:]]
        streaming_result = preprocess_streaming(chunks)
        
        # Core invariant: results must be equal
        assert streaming_result == complete_result
        # Think block should be removed when tag is valid
        assert '<think>' not in streaming_result
        assert '</think>' not in streaming_result
        assert '"boundary": "test6"' in streaming_result
    
    def test_fence_language_boundary_split(self):
        """Test fence language line split across boundaries"""
        # Create content where fence language line split still forms valid fence
        content = "# Test fixture: Fence language split\n```javascript\n{\"boundary\": \"test7\"}\n```"
        
        # Test the invariant: streaming == complete processing
        complete_result = preprocess_complete(content)
        
        # Split in fence language: "```java|script"
        split_pos = content.find('```java') + 7  # Split after "```java" 
        chunks = [content[:split_pos], content[split_pos:]]
        streaming_result = preprocess_streaming(chunks)
        
        # Core invariant: results must be equal
        assert streaming_result == complete_result
        # Content should be extracted when fence is valid
        assert '{"boundary": "test7"}' in streaming_result


class TestFSM:
    """Test the JSON extraction FSM"""
    
    def test_simple_object_extraction(self):
        """Test extracting a simple JSON object"""
        json_text = '{"name": "John", "age": 30}'
        state = JsonFsmState()
        
        fsm_feed(state, json_text)
        result, status = fsm_result(state)
        
        assert status == "DONE"
        assert result == json_text
    
    def test_array_extraction(self):
        """Test extracting JSON array"""
        content = load_fixture("07_array_root.txt")
        # Use complete preprocessing + extraction with finalization
        from app.core.fsm import preprocess_finalize, preprocess_get_result, fsm_finalize
        
        preprocess_state = PreprocessState()
        cleaned = preprocess_chunk(content, preprocess_state)
        # Process carry and get complete result 
        tail = preprocess_finalize(preprocess_state)
        
        fsm_state = JsonFsmState()
        fsm_feed(fsm_state, cleaned + tail)
        fsm_finalize(fsm_state)  # Mark as finalized for upgrade
        result, status = fsm_result(fsm_state)
        
        assert status == "DONE"
        assert result.startswith("[")
        assert result.endswith("]")
        assert '"name": "First"' in result
    
    def test_nested_structures(self):
        """Test nested objects and arrays"""
        content = load_fixture("04_nested.txt")
        state = JsonFsmState()
        
        fsm_feed(state, content)
        result, status = fsm_result(state)
        
        assert status == "DONE"
        # Verify it's parseable JSON
        success, obj, _ = attempt_json_parse(result)
        assert success
        assert "user" in obj
        assert "preferences" in obj["user"]
    
    def test_multiple_json_objects(self):
        """Test FSM picks first complete JSON root when multiple objects present"""
        content = 'Prefix text {"first": 1} middle {"second": 2} suffix'
        
        state = JsonFsmState()
        fsm_feed(state, content)
        fsm_finalize(state)
        result, status = fsm_result(state)
        
        assert status == "DONE"
        assert result == '{"first": 1}', f"Should extract first JSON, got: {result}"
    
    def test_truncated_inside_string_not_repairable(self):
        """Test truncated while inside string should not blindly close braces"""
        content = '{"message": "unterminated string without quote'
        
        state = JsonFsmState()
        fsm_feed(state, content)
        fsm_finalize(state)
        result, status = fsm_result(state)
        
        # Should stay TRUNCATED since we're inside a string
        assert status == "TRUNCATED", f"Should remain TRUNCATED when inside string, got: {status}"
        
        # Repair should not make it parseable by blindly closing
        from app.core.repair import safe_repair, attempt_json_parse
        repaired = safe_repair(result, state)
        success, obj, error = attempt_json_parse(repaired)
        # This should either stay unparseable or have very conservative repair
        assert not success or obj.get("message", "").endswith('unterminated string without quote'), \
            "Should not add quotes inside strings"
    
    def test_escaped_content(self):
        """Test JSON with escaped quotes and backslashes"""
        content = load_fixture("05_escaped_content.txt")
        state = JsonFsmState()
        
        fsm_feed(state, content)
        result, status = fsm_result(state)
        
        assert status == "DONE"
        # Should parse successfully despite escapes
        success, obj, _ = attempt_json_parse(result)
        assert success
        assert "Say \"hello\"" in obj["message"]
    
    def test_truncated_json(self):
        """Test handling of truncated/incomplete JSON"""
        content = load_fixture("03_truncated.txt")
        state = JsonFsmState()
        
        fsm_feed(state, content)
        result, status = fsm_result(state)
        
        assert status == "TRUNCATED"
        assert result.startswith("{")
        # Should capture what was received
        assert "incomplete" in result
    
    def test_streaming_simulation(self):
        """Test FSM with simulated streaming chunks"""
        content = load_fixture("04_nested.txt")
        chunks = simulate_streaming_chunks(content, chunk_size=20)
        
        state = JsonFsmState()
        for chunk in chunks:
            fsm_feed(state, chunk)
        
        result, status = fsm_result(state)
        
        assert status == "DONE"
        # Should produce same result as processing all at once
        success, obj, _ = attempt_json_parse(result)
        assert success
    
    def test_multiple_json_objects(self):
        """Test FSM picks first complete JSON root when multiple objects present"""
        content = 'Prefix text {"first": 1} middle {"second": 2} suffix'
        
        state = JsonFsmState()
        fsm_feed(state, content)
        fsm_finalize(state)
        result, status = fsm_result(state)
        
        assert status == "DONE"
        assert result == '{"first": 1}', f"Should extract first JSON, got: {result}"
    
    def test_truncated_inside_string_not_repairable(self):
        """Test truncated while inside string should not blindly close braces"""
        content = '{"message": "unterminated string without quote'
        
        state = JsonFsmState()
        fsm_feed(state, content)
        fsm_finalize(state)
        result, status = fsm_result(state)
        
        # Should stay TRUNCATED since we're inside a string
        assert status == "TRUNCATED", f"Should remain TRUNCATED when inside string, got: {status}"
        
        # Repair should not make it parseable by blindly closing
        from app.core.repair import safe_repair, attempt_json_parse
        repaired = safe_repair(result, state)
        success, obj, error = attempt_json_parse(repaired)
        # This should either stay unparseable or have very conservative repair
        assert not success or obj.get("message", "").endswith('unterminated string without quote'), \
            "Should not add quotes inside strings"


class TestRepair:
    """Test JSON repair functionality"""
    
    def test_trailing_comma_removal(self):
        """Test removal of trailing commas"""
        content = load_fixture("09_trailing_commas.txt")
        state = JsonFsmState()
        
        fsm_feed(state, content)
        result, status = fsm_result(state)
        
        # Apply repair
        repaired = safe_repair(result, state)
        
        # Should now parse successfully  
        success, obj, error = attempt_json_parse(repaired)
        assert success, f"Parse failed: {error}"
        assert len(obj["items"]) == 2
    
    def test_truncated_repair(self):
        """Test repair of truncated JSON"""
        content = load_fixture("03_truncated.txt")
        state = JsonFsmState()
        
        fsm_feed(state, content)
        result, status = fsm_result(state)
        
        # Apply repair (should close braces)
        repaired = safe_repair(result, state)
        
        # Should now be parseable
        success, obj, error = attempt_json_parse(repaired)
        assert success, f"Parse failed: {error}"
        assert "incomplete" in obj


class TestEndToEnd:
    """End-to-end tests combining preprocessing, FSM, and repair"""
    
    def test_deepseek_pipeline(self):
        """Test complete pipeline with DeepSeek-style output"""
        content = load_fixture("08_deepseek_reasoning.txt")
        
        # Step 1: Preprocess to remove think blocks and fences with finalization
        from app.core.fsm import preprocess_finalize, preprocess_get_result, fsm_finalize
        preprocess_state = PreprocessState()
        cleaned = preprocess_chunk(content, preprocess_state)
        # Process carry
        tail = preprocess_finalize(preprocess_state)
        
        # Step 2: Extract JSON with FSM and finalization
        fsm_state = JsonFsmState()
        fsm_feed(fsm_state, cleaned + tail)
        fsm_finalize(fsm_state)  # Mark as finalized for upgrade
        json_text, fsm_status = fsm_result(fsm_state)
        
        # Step 3: Apply repair if needed
        repaired = safe_repair(json_text, fsm_state)
        
        # Step 4: Verify final JSON
        success, obj, error = attempt_json_parse(repaired)
        
        assert success, f"Pipeline failed: {error}"
        assert fsm_status == "DONE"
        assert "languages" in obj
        assert len(obj["languages"]) == 3
        assert obj["languages"][0]["name"] == "Python"
    
    def test_fenced_with_trailing_commas(self):
        """Test pipeline with fenced JSON that has trailing commas"""
        content = """```json
{
  "items": [
    {"id": 1,},
    {"id": 2,}
  ],
}
```"""
        
        # Full pipeline
        preprocess_state = PreprocessState()
        cleaned = preprocess_chunk(content, preprocess_state)
        
        fsm_state = JsonFsmState()
        fsm_feed(fsm_state, cleaned)
        json_text, _ = fsm_result(fsm_state)
        
        repaired = safe_repair(json_text, fsm_state)
        success, obj, error = attempt_json_parse(repaired)
        
        assert success, f"Pipeline failed: {error}"
        assert len(obj["items"]) == 2
    
    def test_markdown_wrapper_extraction(self):
        """Test extraction from markdown headers and bullet lists"""
        content = """# Analysis Results

## Summary
Here are the findings:

- Item 1
- Item 2

```json
{"results": [{"name": "test", "value": 42}]}
```

## Conclusion
That's the analysis."""
        
        # Full pipeline
        preprocess_state = PreprocessState()
        cleaned = preprocess_chunk(content, preprocess_state)
        tail = preprocess_finalize(preprocess_state)
        
        fsm_state = JsonFsmState()
        fsm_feed(fsm_state, cleaned + tail)
        fsm_finalize(fsm_state)
        json_text, fsm_status = fsm_result(fsm_state)
        
        repaired = safe_repair(json_text, fsm_state)
        success, obj, error = attempt_json_parse(repaired)
        
        assert success, f"Pipeline failed: {error}"
        assert fsm_status == "DONE"
        assert obj["results"][0]["name"] == "test"
        assert obj["results"][0]["value"] == 42
    
    def test_tool_wrapper_extraction(self):
        """Test extraction of tool/function call JSON"""
        content = """I need to call a function:

<function_call>
{"tool": "search", "arguments": {"query": "python tutorial", "limit": 5}}
</function_call>

That should help!"""
        
        # Full pipeline - treat <function_call> like fences
        # This tests the "any structured wrapper" case
        complete_result = preprocess_complete(content)
        
        fsm_state = JsonFsmState() 
        fsm_feed(fsm_state, complete_result)
        fsm_finalize(fsm_state)
        json_text, fsm_status = fsm_result(fsm_state)
        
        repaired = safe_repair(json_text, fsm_state)
        success, obj, error = attempt_json_parse(repaired)
        
        assert success, f"Pipeline failed: {error}"
        assert obj["tool"] == "search"
        assert obj["arguments"]["query"] == "python tutorial"


class TestStreamProcessorIntegration:
    """Integration tests for production stream processor"""
    
    def test_stream_processor_flush_wiring(self):
        """Test stream processor finalization matches complete pipeline"""
        from app.core.stream_processor import JSONStreamProcessor
        from app.core.fsm import JsonFsmState, fsm_feed, fsm_finalize, fsm_result
        
        content = "Here's the result:\n```json\n{\"status\": \"success\", \"data\": [1, 2, 3]}\n```\nDone!"
        
        # Method 1: Stream processor
        processor = JSONStreamProcessor()
        
        # Simulate chunk processing
        chunk1 = "Here's the result:\n```j"
        chunk2 = "son\n{\"status\": \"success\", \"data\": [1,"
        chunk3 = " 2, 3]}\n```\nDone!"
        
        processor.process_chunk(chunk1)
        processor.process_chunk(chunk2) 
        processor.process_chunk(chunk3)
        
        # Get finalized result
        final_result = processor.finalize_extraction()
        
        # Method 2: Complete pipeline
        complete_preprocessed = preprocess_complete(content)
        fsm_state = JsonFsmState()
        fsm_feed(fsm_state, complete_preprocessed)
        fsm_finalize(fsm_state)
        expected_json, expected_status = fsm_result(fsm_state)
        
        # Verify integration
        assert final_result["status"] == expected_status
        assert final_result["json_text"] == expected_json
        assert final_result["parse_ok"] == True
        assert final_result["obj"]["status"] == "success"
        assert final_result["obj"]["data"] == [1, 2, 3]
    
    def test_markdown_wrapper_extraction(self):
        """Test extraction from markdown headers and bullet lists"""
        content = """# Analysis Results

## Summary
Here are the findings:

- Item 1
- Item 2

```json
{"results": [{"name": "test", "value": 42}]}
```

## Conclusion
That's the analysis."""
        
        # Full pipeline
        preprocess_state = PreprocessState()
        cleaned = preprocess_chunk(content, preprocess_state)
        tail = preprocess_finalize(preprocess_state)
        
        fsm_state = JsonFsmState()
        fsm_feed(fsm_state, cleaned + tail)
        fsm_finalize(fsm_state)
        json_text, fsm_status = fsm_result(fsm_state)
        
        repaired = safe_repair(json_text, fsm_state)
        success, obj, error = attempt_json_parse(repaired)
        
        assert success, f"Pipeline failed: {error}"
        assert fsm_status == "DONE"
        assert obj["results"][0]["name"] == "test"
        assert obj["results"][0]["value"] == 42
    
    def test_tool_wrapper_extraction(self):
        """Test extraction of tool/function call JSON"""
        content = """I need to call a function:

<function_call>
{"tool": "search", "arguments": {"query": "python tutorial", "limit": 5}}
</function_call>

That should help!"""
        
        # Full pipeline - treat <function_call> like fences
        # This tests the "any structured wrapper" case
        complete_result = preprocess_complete(content)
        
        fsm_state = JsonFsmState() 
        fsm_feed(fsm_state, complete_result)
        fsm_finalize(fsm_state)
        json_text, fsm_status = fsm_result(fsm_state)
        
        repaired = safe_repair(json_text, fsm_state)
        success, obj, error = attempt_json_parse(repaired)
        
        assert success, f"Pipeline failed: {error}"
        assert obj["tool"] == "search"
        assert obj["arguments"]["query"] == "python tutorial"