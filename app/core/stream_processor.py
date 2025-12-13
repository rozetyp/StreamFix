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

# Global storage for repair results (in production, use Redis/database)
repair_results = {}

class StreamFixer:
    """Processes streaming chat completions with passthrough + retrieve pattern"""
    
    def __init__(self):
        self.processor = JSONStreamProcessor()
        self.request_id: str = str(uuid.uuid4())
        self.content_chunks = []  # Track content for repair, don't buffer output
    
    async def process_stream(self, upstream_stream: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """Passthrough streaming with background repair tracking"""        
        async for chunk in upstream_stream:
            # PASSTHROUGH: Always yield chunks immediately (true streaming)
            yield chunk
            
            if not chunk.strip():
                continue
                
            # Parse SSE format for background processing
            if chunk.startswith("data: "):
                data_part = chunk[6:].strip()
                
                if data_part == "[DONE]":
                    # Finalize repair processing in background
                    final_extraction = self.processor.finalize_extraction()
                    
                    # Store repair result for later retrieval
                    repair_results[self.request_id] = {
                        "status": "REPAIRED" if (final_extraction["parse_ok"] and 
                                               final_extraction["repaired_text"] and 
                                               final_extraction["json_text"] != final_extraction["repaired_text"]) else "PASSTHROUGH",
                        "original_json": final_extraction.get("json_text", ""),
                        "repaired_json": final_extraction.get("repaired_text", ""),
                        "parse_ok": final_extraction.get("parse_ok", False),
                        "error": final_extraction.get("error", None)
                    }
                    continue
                
                try:
                    chunk_data = json.loads(data_part)
                    
                    # Extract content delta for background processing
                    choices = chunk_data.get("choices", [])
                    if choices and "delta" in choices[0]:
                        delta = choices[0]["delta"]
                        if "content" in delta:
                            content_delta = delta["content"]
                            # Process for repair tracking (no buffering)
                            self.processor.process_chunk(content_delta)
                    
                except json.JSONDecodeError:
                    # Ignore malformed chunks for repair processing
                    pass
    
    def get_request_id(self) -> str:
        """Get the request ID for this stream"""
        return self.request_id


async def create_fsm_stream(upstream_response) -> tuple[AsyncGenerator[str, None], str]:
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
    
    return fixer.process_stream(upstream_generator()), fixer.get_request_id()