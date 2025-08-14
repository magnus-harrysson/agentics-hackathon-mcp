#!/usr/bin/env python3
"""
MCP client module for handling MCP server functionality.
This module contains all the MCP-related functionality separated from the main server logic.
"""

import logging
from fastmcp import FastMCP
from api_client import fetch_backstage_api_entity, fetch_backstage_component_relations
from config import config

logger = logging.getLogger("agentics-mcp.mcp_client")

# Create MCP instance
mcp = FastMCP("agentics-mcp")

@mcp.tool()
async def get_server_config() -> str:
    """Get the current server configuration.
    
    Returns:
        Current server configuration including project name, API version, and other settings
    """
    import json
    config_info = config.to_dict()
    return json.dumps(config_info, indent=2)

@mcp.tool()
async def get_backstage_component_relations(component_name: str = "aldente-service") -> str:
    """Fetch a Backstage catalog component entity and return only its relations.
    
    Args:
        component_name: The name of the component to fetch relations for (default: "aldente-service")
        
    Returns:
        The component relations as JSON string, or error message if failed
    """
    return await fetch_backstage_component_relations(component_name)

@mcp.tool()
async def get_backstage_api_entity(entity_name: str = "aldente-service-api", field: str = "") -> str:
    """Fetch a Backstage catalog API entity by name using GitHub token authentication.
    
    Args:
        entity_name: The name of the API entity to fetch from Backstage catalog (default: "aldente-service-api")
        field: Specific field to extract from the entity (e.g., "apiVersion", "spec", "metadata"). If empty, returns full entity.
        
    Returns:
        The API entity information (full or specific field) as JSON string, or error message if failed
    """
    return await fetch_backstage_api_entity(entity_name, field)


async def run_mcp():
    """Run the MCP server."""
    await mcp.run_async()


def get_mcp_instance():
    """Get the MCP instance for external use if needed."""
    return mcp
