"""
Authentication and API key management
"""
import secrets
from typing import Optional, Tuple
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.models.database import ApiKey, Project
from app.db import get_db

# Initialize password hasher for API keys
ph = PasswordHasher()

# Security scheme
security = HTTPBearer()


def generate_api_key() -> str:
    """Generate a new API key"""
    # Format: sfx_<32_chars> (streamfix prefix)
    return f"sfx_{secrets.token_urlsafe(24)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return ph.hash(api_key)


def verify_api_key_hash(api_key: str, hash: str) -> bool:
    """Verify an API key against its hash"""
    try:
        ph.verify(hash, api_key)
        return True
    except VerifyMismatchError:
        return False


async def get_current_project(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Tuple[Project, ApiKey]:
    """
    Dependency to extract and validate API key, return project and key info
    """
    token = credentials.credentials
    
    if not token.startswith("sfx_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db: Session = next(get_db())
    try:
        # Find API key by trying to verify against all stored hashes
        # Note: This is not optimal for large numbers of keys, but fine for v0
        api_keys = db.query(ApiKey).filter(
            ApiKey.revoked_at.is_(None)
        ).all()
        
        api_key_record = None
        for key_record in api_keys:
            if verify_api_key_hash(token, key_record.key_hash):
                api_key_record = key_record
                break
        
        if not api_key_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get project
        project = db.query(Project).filter(
            Project.id == api_key_record.project_id,
            Project.status == "active"
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Project not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last_used_at
        from datetime import datetime
        api_key_record.last_used_at = datetime.utcnow()
        db.commit()
        
        return project, api_key_record
        
    finally:
        db.close()


def create_api_key(db: Session, project_id: str, label: Optional[str] = None) -> Tuple[str, ApiKey]:
    """
    Create a new API key for a project
    Returns (raw_key, api_key_record)
    """
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    
    api_key = ApiKey(
        project_id=project_id,
        key_hash=key_hash,
        label=label
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return raw_key, api_key


def revoke_api_key(db: Session, api_key_id: str) -> bool:
    """Revoke an API key"""
    from datetime import datetime
    
    api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
    if not api_key:
        return False
    
    api_key.revoked_at = datetime.utcnow()
    db.commit()
    return True