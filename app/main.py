"""
StreamFix Gateway - FastAPI application
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.api import chat_noauth, health, demo, streamfix
from app.db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("🚀 Starting StreamFix Gateway...")
    
    # Check if database should be disabled (for testing/validation)
    disable_db = os.getenv("DISABLE_DB", "false").lower() in ["true", "1", "yes"]
    
    if disable_db:
        print("⚠️  Database initialization DISABLED (DISABLE_DB=true)")
    else:
        init_db()
        print("✅ Database initialized")
    
    yield
    # Shutdown
    print("👋 Shutting down StreamFix Gateway...")


app = FastAPI(
    title="StreamFix Gateway",
    description="OpenAI-compatible proxy with streaming JSON repair",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    print(f"{request.method} {request.url} - {response.status_code} ({process_time:.3f}s)")
    
    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    print(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(chat_noauth.router, tags=["Chat"])
app.include_router(streamfix.router, tags=["StreamFix"])
app.include_router(demo.router, tags=["Demo"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)