"""
Database models and table definitions
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate UUID as string for SQLite compatibility"""
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")  # active|paused|deleted
    default_provider = Column(String, nullable=False, default="openrouter")
    default_model = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    api_keys = relationship("ApiKey", back_populates="project")
    upstream_credentials = relationship("UpstreamCredential", back_populates="project")
    schemas = relationship("Schema", back_populates="project")
    request_events = relationship("RequestEvent", back_populates="project")


class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String, nullable=False, unique=True)  # argon2 hash
    label = Column(String, nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="api_keys")


class UpstreamCredential(Base):
    __tablename__ = "upstream_credentials"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)  # openrouter|openai
    api_key_enc = Column(String, nullable=False)  # encrypted API key
    base_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="upstream_credentials")


class Schema(Base):
    __tablename__ = "schemas"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    json_schema = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="schemas")


class RequestEvent(Base):
    __tablename__ = "request_events"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    request_id = Column(String, nullable=False)  # x-request-id or generated
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    api_key_id = Column(String(36), ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True)
    
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    schema_id = Column(String(36), ForeignKey("schemas.id", ondelete="SET NULL"), nullable=True)
    rule_pack_key = Column(String, nullable=True)
    rule_pack_version = Column(Integer, nullable=True)
    
    stream = Column(Boolean, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="UNKNOWN")  # taxonomy enum
    
    latency_ms_total = Column(Integer, nullable=True)
    latency_ms_upstream = Column(Integer, nullable=True) 
    bytes_in = Column(Integer, nullable=True)
    bytes_out = Column(Integer, nullable=True)
    
    # Optional cost fields
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    upstream_cost_usd = Column(String, nullable=True)  # decimal as string for precision
    
    # Diagnostics
    schema_error_paths = Column(JSON, nullable=True)
    error_detail = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="request_events")
    api_key = relationship("ApiKey")
    schema = relationship("Schema")