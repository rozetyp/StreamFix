"""
Streaming JSON processor using FSM for real-time repair
"""
import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from app.core.fsm import PreprocessState, JsonFsmState, preprocess_chunk, preprocess_finalize, preprocess_get_result, fsm_feed, fsm_result


class JSONStreamProcessor:
    """Wrapper class for the FSM-based JSON processing"""
    
    def __init__(self):
        self.preprocess_state = PreprocessState()
        self.fsm_state = JsonFsmState()
        self.accumulated_content = ""
    
    def process_chunk(self, chunk: str) -> str:
        """Process a single chunk and return the processed version"""
        # Preprocess to remove <think> blocks and handle fencing
        processed_chunk = preprocess_chunk(chunk, self.preprocess_state)
        
        # Feed processed chunk to FSM
        if processed_chunk:
            fsm_feed(self.fsm_state, processed_chunk)
        
        # Accumulate for potential JSON repair
        self.accumulated_content += processed_chunk
        
        # For now, just return the preprocessed chunk
        # Full JSON repair happens at the end
        return processed_chunk
    
    def finalize_preprocessing(self) -> str:
        """Finalize preprocessing to handle fence decisions"""
        # Process carry and get complete result with fence decision
        preprocess_finalize(self.preprocess_state)
        return preprocess_get_result(self.preprocess_state)
    
    def finalize_extraction(self) -> dict:
        """Finalize both preprocessing and extraction"""
        from app.core.fsm import fsm_finalize, fsm_feed, fsm_result
        from app.core.repair import safe_repair, attempt_json_parse
        
        # 1) Feed preprocessor tail to FSM
        tail = preprocess_finalize(self.preprocess_state)
        if tail:
            fsm_feed(self.fsm_state, tail)
        
        # 2) Mark FSM as finalized for safe upgrade
        fsm_finalize(self.fsm_state)
        
        # 3) Get result with potential TRUNCATED->DONE upgrade
        json_text, status = fsm_result(self.fsm_state)
        
        if not json_text:
            return {"status": "FAILED", "json_text": None, "repaired_text": None, "parse_ok": False, "obj": None}
        
        # 4) Apply repair
        repaired = safe_repair(json_text, self.fsm_state)
        
        # 5) Parse repaired
        success, obj, error = attempt_json_parse(repaired)
        
        return {
            "status": status,
            "json_text": json_text,
            "repaired_text": repaired,
            "parse_ok": success,
            "obj": obj,
            "error": error
        }
    
    def process_complete(self, complete_text: str) -> str:
        """Process complete text and return repaired version"""
        # Create fresh states for complete processing
        preprocess_state = PreprocessState()
        fsm_state = JsonFsmState()
        
        # Preprocess the complete text
        preprocessed = preprocess_chunk(complete_text, preprocess_state)
        
        # Try to extract and repair JSON
        fsm_feed(fsm_state, preprocessed)
        json_text, status = fsm_result(fsm_state)
        
        if status == "DONE" and json_text:
            try:
                # Validate it's proper JSON
                parsed = json.loads(json_text)
                return json_text
            except json.JSONDecodeError:
                pass
        
        # Return original if no valid JSON found
        return complete_text


import uuid
from typing import Optional

class StreamFixer:
    """Processes streaming chat completions with passthrough + retrieve pattern"""
    
    def __init__(self):
        self.processor = JSONStreamProcessor()
        self.content_chunks = []  # Track content for repair
    
    async def process_stream(self, upstream_stream: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """Process streaming with transparent JSON repair"""        
        async for chunk in upstream_stream:
            # Always yield chunks immediately (true streaming)
            yield chunk
            
            if not chunk.strip():
                continue
                
            # Parse SSE format for content extraction
            if chunk.startswith("data: "):
                data_part = chunk[6:].strip()
                
                if data_part == "[DONE]":
                    continue
                
                try:
                    chunk_data = json.loads(data_part)
                    
                    # Extract content delta for processing
                    choices = chunk_data.get("choices", [])
                    if choices and "delta" in choices[0]:
                        delta = choices[0]["delta"]
                        if "content" in delta:
                            content_delta = delta["content"]
                            # Process chunk for potential repair
                            self.processor.process_chunk(content_delta)
                    
                except json.JSONDecodeError:
                    # Ignore malformed chunks
                    pass

async def create_fsm_stream(upstream_response) -> AsyncGenerator[str, None]:
    """Create FSM-processed stream from upstream response, return (stream, request_id)"""
    fixer = StreamFixer()
    
    async def upstream_generator():
        # Use aiter_bytes() with proper line splitting to preserve SSE format
        buffer = ""
        async for chunk_bytes in upstream_response.aiter_bytes():
            if chunk_bytes:
                buffer += chunk_bytes.decode('utf-8', errors='ignore')
                # Split on newlines and yield complete lines
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():  # Only yield non-empty lines
                        yield line + '\n'
        
        # Yield any remaining buffer content
        if buffer.strip():
            yield buffer
    
    return fixer.process_stream(upstream_generator())