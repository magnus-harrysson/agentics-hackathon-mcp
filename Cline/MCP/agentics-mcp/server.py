#!/usr/bin/env python3
"""
Main server entry point for running both MCP and FastAPI servers.
This server coordinates the startup of both the MCP client and FastAPI client.
"""

import asyncio
import logging
import uvicorn
from fastapi import FastAPI

from api_client import create_api_routes
from mcp_client import run_mcp
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agentics-mcp")

# Create FastAPI app
api = FastAPI(
    title="MCP Server with OpenAPI functionality",
    description="A simple MCP server with FastAPI endpoints for OpenAPI specification retrieval",
    version="1.0.0"
)

# Register API routes from api_client module
create_api_routes(api)


async def run_fastapi():
    """Run the FastAPI server."""
    uvicorn_config = uvicorn.Config(
        app=api,
        host=config.server_host,
        port=config.server_port,
        log_level="info"
    )
    server = uvicorn.Server(uvicorn_config)
    await server.serve()


async def main():
    """Main function to run both MCP and FastAPI servers concurrently."""
    logger.info("Starting both MCP and FastAPI servers...")
    await asyncio.gather(
        run_mcp(),
        run_fastapi()
    )


if __name__ == "__main__":
    asyncio.run(main())
