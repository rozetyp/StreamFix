"""
StreamFix Gateway - Minimal JSON Repair Proxy
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat_noauth, health, streamfix

# Create FastAPI app
app = FastAPI(
    title="StreamFix Gateway",
    description="Real-time JSON repair proxy for AI streaming APIs",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(chat_noauth.router, prefix="/v1", tags=["chat"])
app.include_router(streamfix.router, prefix="/streamfix", tags=["streamfix"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "StreamFix Gateway",
        "version": "1.0.0", 
        "description": "Real-time JSON repair proxy for AI streaming APIs",
        "endpoints": {
            "health": "/health",
            "chat": "/v1/chat/completions",
            "docs": "/docs" if os.getenv("ENVIRONMENT") != "production" else "disabled"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)