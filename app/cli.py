#!/usr/bin/env python3
"""
StreamFix CLI
Simple command-line interface for running StreamFix locally
"""
import os
import sys
import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description='StreamFix - OpenAI-compatible JSON repair proxy')
    parser.add_argument('command', choices=['serve'], help='Command to run')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to (default: 8000)')
    parser.add_argument('--upstream', help='Upstream API base URL (e.g., http://localhost:1234/v1)')
    parser.add_argument('--api-key', help='OpenRouter API key (if using OpenRouter upstream)')
    
    args = parser.parse_args()
    
    if args.command == 'serve':
        # Set environment variables if provided
        if args.upstream:
            os.environ['UPSTREAM_BASE_URL'] = args.upstream
        if args.api_key:
            os.environ['OPENROUTER_API_KEY'] = args.api_key
        
        # Default to local LM Studio if no upstream specified
        if not os.getenv('UPSTREAM_BASE_URL'):
            os.environ['UPSTREAM_BASE_URL'] = 'http://localhost:1234/v1'
            
        print(f"🚀 StreamFix starting on http://{args.host}:{args.port}")
        print(f"📡 Upstream: {os.getenv('UPSTREAM_BASE_URL')}")
        print(f"📖 Point your OpenAI client to: http://{args.host}:{args.port}/v1")
        print("Press CTRL+C to stop")
        
        try:
            uvicorn.run(
                "app.main:app", 
                host=args.host, 
                port=args.port,
                log_level="info"
            )
        except KeyboardInterrupt:
            print("\n👋 StreamFix stopped")


if __name__ == '__main__':
    main()