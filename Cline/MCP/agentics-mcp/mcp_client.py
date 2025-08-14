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
        
        # Get the component relations
        component_relations = await fetch_backstage_component_relations(component_name)
        
        # Parse the relations JSON
        import json
        try:
            relations_data = json.loads(component_relations)
        except json.JSONDecodeError:
            # If it's an error message, return it
            return component_relations
        
        # Start building the Mermaid diagram
        mermaid_lines = [
            "```mermaid",
            "graph TD",
            f"    %% Component: {component_name}",
            f"    {component_name.replace('-', '_').upper()}[{component_name}]",
            ""
        ]
        
        # Track all entities we've seen
        components = set([component_name])
        apis = set()
        groups = set()
        systems = set()
        
        # Process relations
        consumes_apis = []
        provides_apis = []
        depends_on_components = []
        owned_by_groups = []
        part_of_systems = []
        
        for relation in relations_data:
            rel_type = relation.get("type", "")
            target_ref = relation.get("targetRef", "")
            
            if target_ref.startswith("api:default/"):
                api_name = target_ref.replace("api:default/", "")
                apis.add(api_name)
                if rel_type == "consumesApi":
                    consumes_apis.append(api_name)
                elif rel_type == "providesApi":
                    provides_apis.append(api_name)
            elif target_ref.startswith("component:default/"):
                comp_name = target_ref.replace("component:default/", "")
                components.add(comp_name)
                if rel_type == "dependsOn":
                    depends_on_components.append(comp_name)
            elif target_ref.startswith("group:default/"):
                group_name = target_ref.replace("group:default/", "")
                groups.add(group_name)
                if rel_type == "ownedBy":
                    owned_by_groups.append(group_name)
            elif target_ref.startswith("system:default/"):
                system_name = target_ref.replace("system:default/", "")
                systems.add(system_name)
                if rel_type == "partOf":
                    part_of_systems.append(system_name)
        
        # Add all entities to diagram
        for api in apis:
            api_var = api.replace('-', '_').upper()
            mermaid_lines.append(f"    {api_var}[{api}]")
        
        for comp in components:
            if comp != component_name:  # Already added
                comp_var = comp.replace('-', '_').upper()
                mermaid_lines.append(f"    {comp_var}[{comp}]")
        
        for group in groups:
            group_var = group.replace('-', '_').upper()
            mermaid_lines.append(f"    {group_var}[{group}]")
        
        for system in systems:
            system_var = system.replace('-', '_').upper()
            mermaid_lines.append(f"    {system_var}[{system}]")
        
        mermaid_lines.append("")
        
        # Add relationships
        main_comp_var = component_name.replace('-', '_').upper()
        
        for api in consumes_apis:
            api_var = api.replace('-', '_').upper()
            mermaid_lines.append(f"    {main_comp_var} -->|consumes| {api_var}")
        
        for api in provides_apis:
            api_var = api.replace('-', '_').upper()
            mermaid_lines.append(f"    {main_comp_var} -->|provides| {api_var}")
        
        for comp in depends_on_components:
            comp_var = comp.replace('-', '_').upper()
            mermaid_lines.append(f"    {main_comp_var} -.->|depends on| {comp_var}")
        
        for group in owned_by_groups:
            group_var = group.replace('-', '_').upper()
            mermaid_lines.append(f"    {main_comp_var} -.->|owned by| {group_var}")
        
        for system in part_of_systems:
            system_var = system.replace('-', '_').upper()
            mermaid_lines.append(f"    {main_comp_var} -.->|part of| {system_var}")
        
        mermaid_lines.append("")
        
        # Add styling
        mermaid_lines.extend([
            "    %% Styling with good contrast",
            "    classDef service fill:#2196F3,stroke:#1976D2,stroke-width:2px,color:#ffffff",
            "    classDef api fill:#FF9800,stroke:#F57C00,stroke-width:2px,color:#000000",
            "    classDef group fill:#4CAF50,stroke:#388E3C,stroke-width:2px,color:#ffffff",
            "    classDef system fill:#9C27B0,stroke:#7B1FA2,stroke-width:2px,color:#ffffff",
            "",
            f"    class {main_comp_var} service"
        ])
        
        # Classify other components as services (we don't know their actual types from relations)
        other_components = [comp.replace('-', '_').upper() for comp in components if comp != component_name]
        if other_components:
            mermaid_lines.append(f"    class {','.join(other_components)} service")
        
        # Classify APIs
        api_vars = [api.replace('-', '_').upper() for api in apis]
        if api_vars:
            mermaid_lines.append(f"    class {','.join(api_vars)} api")
        
        # Classify groups
        group_vars = [group.replace('-', '_').upper() for group in groups]
        if group_vars:
            mermaid_lines.append(f"    class {','.join(group_vars)} group")
        
        # Classify systems
        system_vars = [system.replace('-', '_').upper() for system in systems]
        if system_vars:
            mermaid_lines.append(f"    class {','.join(system_vars)} system")
        
        mermaid_lines.append("```")
        
        result = "\n".join(mermaid_lines)
        logger.info(f"MCP tool generate_component_dependency_mermaid completed successfully for component: {component_name}")
        return result
        
    except Exception as e:
        logger.error(f"MCP tool generate_component_dependency_mermaid failed for component {component_name}: {e}", exc_info=True)
        import json
        return json.dumps({"error": "MCP tool error", "message": f"Tool execution failed: {str(e)}", "component": component_name}, indent=2)


async def generate_mermaid_for_component(component_name: str) -> str:
    """Generate a Mermaid diagram for a component - direct function for testing."""
    try:
        logger.info(f"Direct function generate_mermaid_for_component called for component: {component_name}")
        
        # Get the component relations
        component_relations = await fetch_backstage_component_relations(component_name)
        
        # Parse the relations JSON
        import json
        try:
            relations_data = json.loads(component_relations)
        except json.JSONDecodeError:
            # If it's an error message, return it
            return component_relations
        
        # Start building the Mermaid diagram
        mermaid_lines = [
            "```mermaid",
            "graph TD",
            f"    %% Component: {component_name}",
            f"    {component_name.replace('-', '_').upper()}[{component_name}]",
            ""
        ]
        
        # Track all entities we've seen
        components = set([component_name])
        apis = set()
        groups = set()
        systems = set()
        
        # Process relations
        consumes_apis = []
        provides_apis = []
        depends_on_components = []
        owned_by_groups = []
        part_of_systems = []
        
        for relation in relations_data:
            rel_type = relation.get("type", "")
            target_ref = relation.get("targetRef", "")
            
            if target_ref.startswith("api:default/"):
                api_name = target_ref.replace("api:default/", "")
                apis.add(api_name)
                if rel_type == "consumesApi":
                    consumes_apis.append(api_name)
                elif rel_type == "providesApi":
                    provides_apis.append(api_name)
            elif target_ref.startswith("component:default/"):
                comp_name = target_ref.replace("component:default/", "")
                components.add(comp_name)
                if rel_type == "dependsOn":
                    depends_on_components.append(comp_name)
            elif target_ref.startswith("group:default/"):
                group_name = target_ref.replace("group:default/", "")
                groups.add(group_name)
                if rel_type == "ownedBy":
                    owned_by_groups.append(group_name)
            elif target_ref.startswith("system:default/"):
                system_name = target_ref.replace("system:default/", "")
                systems.add(system_name)
                if rel_type == "partOf":
                    part_of_systems.append(system_name)
        
        # Add all entities to diagram
        for api in apis:
            api_var = api.replace('-', '_').upper()
            mermaid_lines.append(f"    {api_var}[{api}]")
        
        for comp in components:
            if comp != component_name:  # Already added
                comp_var = comp.replace('-', '_').upper()
                mermaid_lines.append(f"    {comp_var}[{comp}]")
        
        for group in groups:
            group_var = group.replace('-', '_').upper()
            mermaid_lines.append(f"    {group_var}[{group}]")
        
        for system in systems:
            system_var = system.replace('-', '_').upper()
            mermaid_lines.append(f"    {system_var}[{system}]")
        
        mermaid_lines.append("")
        
        # Add relationships
        main_comp_var = component_name.replace('-', '_').upper()
        
        for api in consumes_apis:
            api_var = api.replace('-', '_').upper()
            mermaid_lines.append(f"    {main_comp_var} -->|consumes| {api_var}")
        
        for api in provides_apis:
            api_var = api.replace('-', '_').upper()
            mermaid_lines.append(f"    {main_comp_var} -->|provides| {api_var}")
        
        for comp in depends_on_components:
            comp_var = comp.replace('-', '_').upper()
            mermaid_lines.append(f"    {main_comp_var} -.->|depends on| {comp_var}")
        
        for group in owned_by_groups:
            group_var = group.replace('-', '_').upper()
            mermaid_lines.append(f"    {main_comp_var} -.->|owned by| {group_var}")
        
        for system in part_of_systems:
            system_var = system.replace('-', '_').upper()
            mermaid_lines.append(f"    {main_comp_var} -.->|part of| {system_var}")
        
        mermaid_lines.append("")
        
        # Add styling
        mermaid_lines.extend([
            "    %% Styling with good contrast",
            "    classDef service fill:#2196F3,stroke:#1976D2,stroke-width:2px,color:#ffffff",
            "    classDef api fill:#FF9800,stroke:#F57C00,stroke-width:2px,color:#000000",
            "    classDef group fill:#4CAF50,stroke:#388E3C,stroke-width:2px,color:#ffffff",
            "    classDef system fill:#9C27B0,stroke:#7B1FA2,stroke-width:2px,color:#ffffff",
            "",
            f"    class {main_comp_var} service"
        ])
        
        # Classify other components as services (we don't know their actual types from relations)
        other_components = [comp.replace('-', '_').upper() for comp in components if comp != component_name]
        if other_components:
            mermaid_lines.append(f"    class {','.join(other_components)} service")
        
        # Classify APIs
        api_vars = [api.replace('-', '_').upper() for api in apis]
        if api_vars:
            mermaid_lines.append(f"    class {','.join(api_vars)} api")
        
        # Classify groups
        group_vars = [group.replace('-', '_').upper() for group in groups]
        if group_vars:
            mermaid_lines.append(f"    class {','.join(group_vars)} group")
        
        # Classify systems
        system_vars = [system.replace('-', '_').upper() for system in systems]
        if system_vars:
            mermaid_lines.append(f"    class {','.join(system_vars)} system")
        
        mermaid_lines.append("```")
        
        result = "\n".join(mermaid_lines)
        logger.info(f"Direct function generate_mermaid_for_component completed successfully for component: {component_name}")
        return result
        
    except Exception as e:
        logger.error(f"Direct function generate_mermaid_for_component failed for component {component_name}: {e}", exc_info=True)
        import json
        return json.dumps({"error": "Direct function error", "message": f"Function execution failed: {str(e)}", "component": component_name}, indent=2)


async def run_mcp():
    """Run the MCP server."""
    await mcp.run_async()


def get_mcp_instance():
    """Get the MCP instance for external use if needed."""
    return mcp
