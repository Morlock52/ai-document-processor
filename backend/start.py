#!/usr/bin/env python3
"""
Startup script for the backend with dynamic port configuration
"""
import os
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    # Load .env.ports if it exists
    if os.path.exists('.env.ports'):
        from dotenv import load_dotenv
        load_dotenv('.env.ports', override=True)
    
    # Get port from settings
    port = settings.PORT
    host = settings.HOST
    
    print(f"Starting Document Processor API on {host}:{port}")
    print(f"API documentation will be available at http://localhost:{port}/docs")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )