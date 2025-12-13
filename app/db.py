"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.models.database import Base

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./streamfix_dev.db")

# Create engine
if "sqlite" in DATABASE_URL:
    # SQLite for local development/testing
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
else:
    # PostgreSQL for production
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def init_db():
    """Initialize database with tables and default data"""
    create_tables()
    
    # Create a default project for testing
    db = SessionLocal()
    try:
        from app.models.database import Project, UpstreamCredential
        from app.core.crypto import encrypt_api_key
        
        # Check if we already have a default project
        existing = db.query(Project).filter(Project.name == "Default").first()
        if existing:
            return
        
        # Create default project
        project = Project(
            name="Default",
            status="active", 
            default_provider="openrouter",
            default_model="anthropic/claude-3.5-sonnet"
        )
        db.add(project)
        db.flush()  # Get the ID
        
        # Add upstream credential if API key is provided
        upstream_key = os.getenv("OPENROUTER_API_KEY")
        if upstream_key:
            credential = UpstreamCredential(
                project_id=project.id,
                provider="openrouter",
                api_key_enc=encrypt_api_key(upstream_key),
                base_url="https://openrouter.ai/api/v1"
            )
            db.add(credential)
        
        db.commit()
        print(f"Created default project with ID: {project.id}")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()