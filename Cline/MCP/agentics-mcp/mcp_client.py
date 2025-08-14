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
    fetch_backstage_components_by_system,
    fetch_deprecated_entities
)
from config import config
from mermaid_generator import generate_component_dependency_diagram, generate_systems_overview_diagram, generate_single_system_diagram

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

@mcp.tool()
async def generate_systems_overview_mermaid(base_url: str = "") -> str:
    """Generate a Mermaid diagram showing all systems with team ownership boundaries using only Backstage API data.
    
    Args:
        base_url: Optional base URL override for Backstage API (if empty, uses configured default)
        
    Returns:
        Mermaid diagram as string showing all systems with team boundaries, or error message if failed
    """
    try:
        logger.info("MCP tool generate_systems_overview_mermaid called")
        result = await generate_systems_overview_diagram()
        logger.info("MCP tool generate_systems_overview_mermaid completed successfully")
        return result
    except Exception as e:
        logger.error(f"MCP tool generate_systems_overview_mermaid failed: {e}", exc_info=True)
        import json
        return json.dumps({"error": "MCP tool error", "message": f"Tool execution failed: {str(e)}"}, indent=2)

@mcp.tool()
async def generate_component_dependency_mermaid(component_name: str, base_url: str = "") -> str:
    """Generate a Mermaid diagram for a component and all its dependencies using only Backstage API data.
    
    Args:
        component_name: The name of the component to generate diagram for (required)
        base_url: Optional base URL override for Backstage API (if empty, uses configured default)
        
    Returns:
        Mermaid diagram as string showing component dependencies, or error message if failed
    """
    try:
        logger.info(f"MCP tool generate_component_dependency_mermaid called for component: {component_name}")
        result = await generate_component_dependency_diagram(component_name)
        logger.info(f"MCP tool generate_component_dependency_mermaid completed successfully for component: {component_name}")
        return result
    except Exception as e:
        logger.error(f"MCP tool generate_component_dependency_mermaid failed for component {component_name}: {e}", exc_info=True)
        import json
        return json.dumps({"error": "MCP tool error", "message": f"Tool execution failed: {str(e)}", "component": component_name}, indent=2)

@mcp.tool()
async def generate_single_system_mermaid(system_name: str, base_url: str = "") -> str:
    """Generate a Mermaid diagram for a single system showing its components and relationships using only Backstage API data.
    
    Args:
        system_name: The name of the system to generate diagram for (required)
        base_url: Optional base URL override for Backstage API (if empty, uses configured default)
        
    Returns:
        Mermaid diagram as string showing single system architecture, or error message if failed
    """
    try:
        logger.info(f"MCP tool generate_single_system_mermaid called for system: {system_name}")
        result = await generate_single_system_diagram(system_name)
        logger.info(f"MCP tool generate_single_system_mermaid completed successfully for system: {system_name}")
        return result
    except Exception as e:
        logger.error(f"MCP tool generate_single_system_mermaid failed for system {system_name}: {e}", exc_info=True)
        import json
        return json.dumps({"error": "MCP tool error", "message": f"Tool execution failed: {str(e)}", "system": system_name}, indent=2)

@mcp.tool()
async def list_deprecated_entities(base_url: str = "") -> str:
    """List all deprecated entities (APIs and components) from Backstage catalog.
    
    Args:
        base_url: Optional base URL override for Backstage API (if empty, uses configured default)
        
    Returns:
        List of deprecated entity names with their types as JSON string, or error message if failed
    """
    try:
        logger.info("MCP tool list_deprecated_entities called")
        url_override = base_url if base_url else None
        result = await fetch_deprecated_entities(url_override)
        logger.info("MCP tool list_deprecated_entities completed successfully")
        return result
    except Exception as e:
        logger.error(f"MCP tool list_deprecated_entities failed: {e}", exc_info=True)
        import json
        return json.dumps({"error": "MCP tool error", "message": f"Tool execution failed: {str(e)}"}, indent=2)

@mcp.tool()
async def generate_api_migration_plan(from_api: str, to_api: str, base_url: str = "") -> str:
    """Generate a detailed migration plan from one API version to another with Python code examples.
    
    This tool analyzes both API specifications, validates that proper relations exist in Backstage,
    and provides comprehensive migration guidance including code snippets and breaking changes.
    
    Args:
        from_api: The name of the source API to migrate from (e.g., "payments-api-v1")
        to_api: The name of the target API to migrate to (e.g., "payments-api-v2")
        base_url: Optional base URL override for Backstage API (if empty, uses configured default)
        
    Returns:
        Detailed migration plan with Python code examples as JSON string, or error message if failed
    """
    try:
        logger.info(f"MCP tool generate_api_migration_plan called: {from_api} -> {to_api}")
        
        # Import the migration generator function
        from mermaid_generator import generate_api_migration_plan_internal
        
        result = await generate_api_migration_plan_internal(from_api, to_api, base_url)
        logger.info(f"MCP tool generate_api_migration_plan completed successfully: {from_api} -> {to_api}")
        return result
    except Exception as e:
        logger.error(f"MCP tool generate_api_migration_plan failed: {e}", exc_info=True)
        import json
        return json.dumps({"error": "MCP tool error", "message": f"Tool execution failed: {str(e)}", "from_api": from_api, "to_api": to_api}, indent=2)

# Direct functions for testing
async def generate_systems_overview_mermaid_direct() -> str:
    """Generate a systems overview Mermaid diagram - direct function for testing."""
    return await generate_systems_overview_diagram()

async def generate_mermaid_for_component(component_name: str) -> str:
    """Generate a Mermaid diagram for a component - direct function for testing."""
    return await generate_component_dependency_diagram(component_name)

async def run_mcp():
    """Run the MCP server."""
    await mcp.run_async()

def get_mcp_instance():
    """Get the MCP instance for external use if needed."""
    return mcp
