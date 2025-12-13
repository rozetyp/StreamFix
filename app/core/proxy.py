"""
Proxy functionality for calling upstream providers
"""
import time
import httpx
from typing import Dict, Any, Optional, AsyncGenerator
from app.models.database import Project, UpstreamCredential
from app.core.crypto import decrypt_api_key
from sqlalchemy.orm import Session


class UpstreamProvider:
    """Base class for upstream provider clients"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=90.0)
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for upstream requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat_completion(
        self, 
        request_body: Dict[str, Any], 
        stream: bool = False
    ) -> Dict[str, Any] | AsyncGenerator[bytes, None]:
        """
        Call upstream chat completion API
        Returns dict for non-stream, AsyncGenerator for stream
        """
        url = f"{self.base_url}/chat/completions"
        headers = self.get_headers()
        
        if stream:
            return self._stream_completion(url, headers, request_body)
        else:
            return await self._non_stream_completion(url, headers, request_body)
    
    async def _non_stream_completion(self, url: str, headers: Dict[str, str], body: Dict[str, Any]) -> Dict[str, Any]:
        """Non-streaming completion"""
        response = await self.client.post(url, json=body, headers=headers)
        response.raise_for_status()
        return response.json()
    
    async def _stream_completion(self, url: str, headers: Dict[str, str], body: Dict[str, Any]) -> AsyncGenerator[bytes, None]:
        """Streaming completion"""
        body["stream"] = True
        
        async with self.client.stream("POST", url, json=body, headers=headers) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                yield chunk
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class OpenRouterProvider(UpstreamProvider):
    """OpenRouter-specific provider"""
    
    def get_headers(self) -> Dict[str, str]:
        headers = super().get_headers()
        headers.update({
            "HTTP-Referer": "https://streamfix.dev",  # Required by OpenRouter
            "X-Title": "StreamFix Gateway"
        })
        return headers


class OpenAIProvider(UpstreamProvider):
    """OpenAI-specific provider"""
    pass


def get_provider_client(project: Project, db: Session) -> UpstreamProvider:
    """
    Get the appropriate provider client for a project
    """
    # Get upstream credentials
    credential = db.query(UpstreamCredential).filter(
        UpstreamCredential.project_id == project.id,
        UpstreamCredential.provider == project.default_provider,
        UpstreamCredential.revoked_at.is_(None)
    ).first()
    
    if not credential:
        raise ValueError(f"No active credentials found for provider {project.default_provider}")
    
    # Decrypt API key
    api_key = decrypt_api_key(credential.api_key_enc)
    
    # Return appropriate provider
    if credential.provider == "openrouter":
        return OpenRouterProvider(credential.base_url, api_key)
    elif credential.provider == "openai":
        return OpenAIProvider(credential.base_url, api_key)
    else:
        raise ValueError(f"Unknown provider: {credential.provider}")


async def log_request_event(
    db: Session,
    project_id: str,
    api_key_id: str,
    request_id: str,
    provider: str,
    model: str,
    stream: bool,
    status: str = "UNKNOWN",
    **kwargs
):
    """Log a request event to the database"""
    from app.models.database import RequestEvent
    
    event = RequestEvent(
        project_id=project_id,
        api_key_id=api_key_id,
        request_id=request_id,
        provider=provider,
        model=model,
        stream=stream,
        status=status,
        **kwargs
    )
    
    db.add(event)
    db.commit()