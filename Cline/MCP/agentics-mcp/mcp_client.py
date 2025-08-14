#!/usr/bin/env python3
"""
MCP client module for handling MCP server functionality.
This module contains all the MCP-related functionality separated from the main server logic.
"""

import logging
from fastmcp import FastMCP
from api_client import (
    fetch_backstage_api_entity, 
    fetch_backstage_component_relations,
    fetch_backstage_systems,
    fetch_backstage_components_by_system
)
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

@mcp.tool()
async def list_backstage_systems(base_url: str = "") -> str:
    """List all systems from Backstage catalog by querying components and extracting their systems.
    
    Args:
        base_url: Optional base URL override for Backstage API (if empty, uses configured default)
        
    Returns:
        List of unique systems with counts as JSON string, or error message if failed
    """
    try:
        logger.info("MCP tool list_backstage_systems called")
        url_override = base_url if base_url else None
        result = await fetch_backstage_systems(url_override)
        logger.info("MCP tool list_backstage_systems completed successfully")
        return result
    except Exception as e:
        logger.error(f"MCP tool list_backstage_systems failed: {e}", exc_info=True)
        import json
        return json.dumps({"error": "MCP tool error", "message": f"Tool execution failed: {str(e)}"}, indent=2)

@mcp.tool()
async def list_backstage_components_by_system(system_name: str, base_url: str = "") -> str:
    """List all components for a specific system from Backstage catalog.
    
    Args:
        system_name: The name of the system to filter components by (required)
        base_url: Optional base URL override for Backstage API (if empty, uses configured default)
        
    Returns:
        List of components in the system with detailed information as JSON string, or error message if failed
    """
    try:
        logger.info(f"MCP tool list_backstage_components_by_system called for system: {system_name}")
        url_override = base_url if base_url else None
        result = await fetch_backstage_components_by_system(system_name, url_override)
        logger.info(f"MCP tool list_backstage_components_by_system completed successfully for system: {system_name}")
        return result
    except Exception as e:
        logger.error(f"MCP tool list_backstage_components_by_system failed for system {system_name}: {e}", exc_info=True)
        import json
        return json.dumps({"error": "MCP tool error", "message": f"Tool execution failed: {str(e)}", "system": system_name}, indent=2)


async def run_mcp():
    """Run the MCP server."""
    await mcp.run_async()


def get_mcp_instance():
    """Get the MCP instance for external use if needed."""
    return mcp
