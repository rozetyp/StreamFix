from dataclasses import dataclass, field
from typing import List

@dataclass 
class PreprocessState:
    """State for streaming-safe preprocessing"""
    in_think: bool = False
    fence_open: bool = False
    fence_lang_captured: bool = False
    carry: str = ""  # Buffer for partial tokens across chunks
    has_fences: bool = False  # Track if we've seen any fences
    fence_only_content: str = ""  # Content found only inside fences
    all_content: str = ""  # All content (minus think blocks and fence markers)

@dataclass
class JsonFsmState:
    """State for JSON extraction finite state machine"""
    state: str = "SEEK_START"  # SEEK_START | IN_JSON | DONE | FAILED
    depth: int = 0
    in_string: bool = False
    escape: bool = False
    started_with: str = ""  # '{' or '['
    buf: List[str] = field(default_factory=list)
    max_chars: int = 200_000

THINK_OPEN = "<think>"
THINK_CLOSE = "</think>"
FENCE = "```"
TAIL = 7  # max(len("</think>"), len("<think>"), len("```")) - 1

def preprocess_chunk(text: str, state: PreprocessState) -> str:
    """
    Streaming-safe preprocessing with two-candidate approach.
    Accumulates both fence-only and all-content streams.
    """
    buf = (state.carry or "") + (text or "")
    if not buf:
        return ""

    # Always keep tail for next chunk, except handle empty tail case
    if len(buf) <= TAIL:
        state.carry = buf
        return ""
    
    cut = len(buf) - TAIL
    body, tail = buf[:cut], buf[cut:]

    immediate_out = []  # For immediate compatibility
    i = 0
    
    while i < len(body):
        # Handle <think> blocks
        if body.startswith(THINK_OPEN, i):
            state.in_think = True
            i += len(THINK_OPEN)
            continue
        
        if state.in_think and body.startswith(THINK_CLOSE, i):
            state.in_think = False
            i += len(THINK_CLOSE)
            continue
        
        # Handle ``` fences
        if body.startswith(FENCE, i):
            state.has_fences = True
            if not state.fence_open:
                state.fence_open = True
                state.fence_lang_captured = False
            else:
                state.fence_open = False
                state.fence_lang_captured = False
            i += len(FENCE)
            continue

        c = body[i]

        # Skip content inside <think> blocks
        if state.in_think:
            i += 1
            continue

        # Handle fence content - skip language tag line
        if state.fence_open and not state.fence_lang_captured:
            if c == "\n":
                state.fence_lang_captured = True
            i += 1
            continue
            
        # Accumulate in appropriate streams
        if state.fence_open:
            # Inside fences: add to fence-only stream
            state.fence_only_content += c
        
        # Always add to all-content stream
        state.all_content += c
        immediate_out.append(c)
        i += 1

    state.carry = tail
    return "".join(immediate_out)

    state.carry = tail
    return "".join(out)


def preprocess_finalize(state: PreprocessState) -> str:
    """Process remaining carry and return just the processed tail"""
    if not state.carry:
        return ""
        
    final_chunk = state.carry
    state.carry = ""
    
    # Process the carry through the same logic
    processed_tail = ""
    i = 0
    while i < len(final_chunk):
        # Handle <think> blocks
        if final_chunk.startswith(THINK_OPEN, i):
            state.in_think = True
            i += len(THINK_OPEN)
            continue
        
        if state.in_think and final_chunk.startswith(THINK_CLOSE, i):
            state.in_think = False
            i += len(THINK_CLOSE)
            continue
        
        # Handle ``` fences
        if final_chunk.startswith(FENCE, i):
            state.has_fences = True
            if not state.fence_open:
                state.fence_open = True
                state.fence_lang_captured = False
            else:
                state.fence_open = False
                state.fence_lang_captured = False
            i += len(FENCE)
            continue

        c = final_chunk[i]

        # Skip content inside <think> blocks
        if state.in_think:
            i += 1
            continue

        # Handle fence content - skip language tag line
        if state.fence_open and not state.fence_lang_captured:
            if c == "\n":
                state.fence_lang_captured = True
            i += 1
            continue
            
        # Accumulate in appropriate streams
        if state.fence_open:
            state.fence_only_content += c
        
        state.all_content += c
        processed_tail += c
        i += 1

    return processed_tail


def preprocess_get_result(state: PreprocessState) -> str:
    """Get final result after finalization - make fence decision"""
    if state.has_fences:
        return state.fence_only_content
    else:
        return state.all_content


def preprocess_streaming(chunks: list[str]) -> str:
    """Test helper: process chunks with proper fence decision"""
    state = PreprocessState()
    
    # Process all chunks
    for chunk in chunks:
        preprocess_chunk(chunk, state)
    
    # Process final carry
    preprocess_finalize(state)
    
    # Get final result with fence decision
    return preprocess_get_result(state)
    state = PreprocessState()
    
    for chunk in chunks:
        preprocess_chunk(chunk, state)
    
    # Process final carry
    preprocess_finalize(state)
    
    # Make the fence decision just like preprocess_complete
    if state.has_seen_fences:
        return state.accumulated_fence_content
    else:
        return state.accumulated_non_fence_content
    """Process any remaining content in carry buffer and return appropriate result"""
    # Process any remaining carry
    if state.carry:
        final_chunk = state.carry
        state.carry = ""
        
        fence_content = []
        non_fence_content = []
        i = 0
        
        while i < len(final_chunk):
            # Handle <think> blocks
            if final_chunk.startswith(THINK_OPEN, i):
                state.in_think = True
                i += len(THINK_OPEN)
                continue
            
            if state.in_think and final_chunk.startswith(THINK_CLOSE, i):
                state.in_think = False
                i += len(THINK_CLOSE)
                continue
            
            # Handle ``` fences
            if final_chunk.startswith(FENCE, i):
                state.has_seen_fences = True
                if not state.fence_open:
                    state.fence_open = True
                    state.fence_lang_captured = False
                else:
                    state.fence_open = False
                    state.fence_lang_captured = False
                i += len(FENCE)
                continue

            c = final_chunk[i]

            # Skip content inside <think> blocks
            if state.in_think:
                i += 1
                continue

            # Handle fence content
            if state.fence_open:
                if not state.fence_lang_captured:
                    if c == "\n":
                        state.fence_lang_captured = True
                    i += 1
                    continue
                fence_content.append(c)
                i += 1
                continue

            # Outside fence and not in think
            non_fence_content.append(c)
            i += 1

        # Add final content to accumulated totals
        state.accumulated_fence_content += "".join(fence_content)
        state.accumulated_non_fence_content += "".join(non_fence_content)

    # Make global decision: if any fences were seen, return only fence content
    if state.has_seen_fences:
        return state.accumulated_fence_content
    else:
        return state.accumulated_non_fence_content


def preprocess_complete(text: str) -> str:
    """
    Process complete text in one shot (for single-chunk scenarios)
    """
    if not text:
        return ""
    
    out = []
    fence_out = []  # Collect content inside fences
    i = 0
    in_think = False
    fence_open = False
    fence_lang_captured = False
    has_fences = False  # Track if we ever see any fences
    
    while i < len(text):
        # Handle <think> blocks
        if text.startswith(THINK_OPEN, i):
            in_think = True
            i += len(THINK_OPEN)
            continue
        
        if in_think and text.startswith(THINK_CLOSE, i):
            in_think = False
            i += len(THINK_CLOSE)
            continue
        
        # Handle ``` fences
        if text.startswith(FENCE, i):
            has_fences = True  # Mark that we found fences
            # Toggle fence state
            if not fence_open:
                fence_open = True
                fence_lang_captured = False
            else:
                fence_open = False
                fence_lang_captured = False
            i += len(FENCE)
            continue

        c = text[i]

        # Skip content inside <think> blocks
        if in_think:
            i += 1
            continue

        # Handle fence content
        if fence_open:
            # Skip fence language tag line until newline
            if not fence_lang_captured:
                if c == "\n":
                    fence_lang_captured = True
                i += 1
                continue
            # Inside fenced content - add to fence output
            fence_out.append(c)
            i += 1
            continue

        # Outside fence and not in think: add to general output
        out.append(c)
        i += 1

    # Return fenced content if any fences were found, otherwise return general content
    if has_fences:
        return "".join(fence_out)
    else:
        return "".join(out)


def fsm_feed(state: JsonFsmState, text: str, root: str = None) -> None:
    """
    Feed preprocessed characters into FSM.
    root: "object"|"array"|None (if None, accept '{' or '[')
    """
    if state.state in ("DONE", "FAILED"):
        return
    
    for ch in text:
        if state.state == "SEEK_START":
            if root == "object" and ch != "{":
                continue
            if root == "array" and ch != "[":
                continue
            if ch == "{" or ch == "[":
                state.state = "IN_JSON"
                state.started_with = ch
                state.depth = 1
                state.buf.append(ch)
            else:
                continue
            continue
        
        # IN_JSON state
        state.buf.append(ch)
        
        if state.in_string:
            if state.escape:
                state.escape = False
                continue
            if ch == "\\":
                state.escape = True
                continue
            if ch == '"':
                state.in_string = False
            continue
        
        # not in string
        if ch == '"':
            state.in_string = True
            continue
        
        if ch in "{[":
            state.depth += 1
        elif ch in "}]":
            state.depth -= 1
            if state.depth == 0:
                state.state = "DONE"
                return
        
        if len(state.buf) >= state.max_chars:
            state.state = "FAILED"
            return


def fsm_finalize(state: JsonFsmState) -> None:
    """
    Mark FSM as finalized - enables TRUNCATED->DONE upgrade when safe
    """
    if state.state == "IN_JSON" and not state.in_string and state.buf:
        state.completable = True


def fsm_result(state: JsonFsmState) -> tuple[str, str]:
    """
    Returns (json_text_or_empty, status)
    status: DONE | TRUNCATED | FAILED
    """
    if state.state == "DONE":
        return ("".join(state.buf), "DONE")
    if state.state == "IN_JSON":
        json_text = "".join(state.buf)
        # Upgrade TRUNCATED->DONE if safe and finalized
        if getattr(state, 'completable', False) and not state.in_string and json_text:
            return (json_text, "DONE")
        return (json_text, "TRUNCATED")
    return ("", "FAILED")


def extract_json_from_content(content: str) -> tuple[str, str]:
    """
    Extract JSON from mixed content (think blocks, fences, prose).
    Returns (extracted_json, status)
    status: DONE | TRUNCATED | FAILED
    """
    if not content:
        return "", "FAILED"
    
    # Step 1: Preprocess to remove think blocks and handle fences
    preprocess_state = PreprocessState()
    preprocess_chunk(content, preprocess_state)
    preprocess_finalize(preprocess_state)
    clean_content = preprocess_get_result(preprocess_state)
    
    # Step 2: Run FSM extraction on cleaned content
    fsm_state = JsonFsmState()
    fsm_feed(fsm_state, clean_content)
    fsm_finalize(fsm_state)
    
    # Step 3: Get final result
    return fsm_result(fsm_state)