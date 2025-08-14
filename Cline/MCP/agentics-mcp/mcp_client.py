#!/usr/bin/env python3
"""
MCP client module for handling MCP server functionality.
This module contains all the MCP-related functionality separated from the main server logic.
"""

import logging
from fastmcp import FastMCP
from api_client import fetch_openapi_spec, get_api_info

logger = logging.getLogger("agentics-mcp.mcp_client")

# Create MCP instance
mcp = FastMCP("agentics-mcp")


@mcp.tool()
async def fetch_api_specs(format: str = "json", save_to_file: str = None) -> str:
    """Fetch the PET API (Swagger Petstore) OpenAPI specification.
    
    Args:
        format: The format to return the specification in ("json" or "yaml")
        save_to_file: Optional file path to save the specification to. If provided, the spec will be saved to this file.
        
    Returns:
        The OpenAPI specification in the requested format, or a success message if saved to file
    """
    return await fetch_openapi_spec(format, save_to_file)


@mcp.tool()
async def get_api_infos() -> str:
    """Get basic information about the PET API specification.
    
    Returns:
        Basic information about the PET API including title, version, and description
    """
    return await get_api_info()


async def run_mcp():
    """Run the MCP server."""
    await mcp.run_async()


def get_mcp_instance():
    """Get the MCP instance for external use if needed."""
    return mcp
