#!/usr/bin/env python3
"""
MCP-only server entry point.
This server runs only the MCP functionality without the FastAPI server.
"""

import asyncio
import logging
from mcp_client import run_mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agentics-mcp")


async def main():
    """Main function to run only the MCP server."""
    logger.info("Starting MCP server only...")
    await run_mcp()


if __name__ == "__main__":
    asyncio.run(main())
