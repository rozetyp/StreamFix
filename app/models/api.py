"""
Pydantic models for API requests and responses
"""
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# OpenAI-compatible types
Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    role: Role
    content: Union[str, List[Dict[str, Any]], None] = None
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


class StreamFixMetadata(BaseModel):
    """StreamFix-specific configuration embedded in metadata field"""
    project_id: Optional[str] = None
    schema_id: Optional[str] = None
    rule_pack_key: Optional[str] = None  # e.g. "default", "deepseek_r1"
    json_root: Optional[Literal["object", "array"]] = None


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible request with StreamFix extensions"""
    model_config = ConfigDict(extra="allow")  # Allow OpenAI-compatible extras

    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    
    # StreamFix configuration (tucked inside metadata to avoid breaking clients)
    metadata: Optional[Dict[str, Any]] = None

    def streamfix(self) -> StreamFixMetadata:
        """Extract StreamFix metadata safely"""
        if not self.metadata or not isinstance(self.metadata, dict):
            return StreamFixMetadata()
        
        sf_data = self.metadata.get("streamfix", {})
        if not isinstance(sf_data, dict):
            return StreamFixMetadata()
            
        return StreamFixMetadata(**sf_data)


# Admin API models
class ProjectCreate(BaseModel):
    name: str
    default_provider: Literal["openrouter", "openai"] = "openrouter"
    default_model: Optional[str] = None


class ProjectOut(BaseModel):
    id: str
    name: str
    status: str
    default_provider: str
    default_model: Optional[str]
    created_at: datetime


class SchemaUpsert(BaseModel):
    name: str
    json_schema: Dict[str, Any]


class SchemaOut(BaseModel):
    id: str
    name: str
    json_schema: Dict[str, Any]
    created_at: datetime


class ApiKeyCreate(BaseModel):
    label: Optional[str] = None


class ApiKeyOut(BaseModel):
    id: str
    label: Optional[str]
    created_at: datetime
    revoked_at: Optional[datetime] = None


class CreateApiKeyResponse(BaseModel):
    api_key: str
    api_key_id: str


class RequestEventOut(BaseModel):
    id: str
    request_id: str
    created_at: datetime
    provider: str
    model: str
    schema_id: Optional[str]
    status: str
    attempts: int
    latency_ms_total: Optional[int]
    bytes_in: Optional[int]
    bytes_out: Optional[int]
    total_tokens: Optional[int]
    upstream_cost_usd: Optional[float]
    schema_error_paths: Optional[List[str]] = None
    error_detail: Optional[Dict[str, Any]] = None


class EventsQuery(BaseModel):
    """Query parameters for events API"""
    status: Optional[str] = None
    model: Optional[str] = None
    schema_id: Optional[str] = None
    since: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=500)


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    
    
class OverviewResponse(BaseModel):
    """Dashboard overview data"""
    total_requests: int
    success_rate: float
    avg_latency_ms: Optional[float]
    top_failures: List[Dict[str, Any]]
    period: str  # "24h", "7d", etc.