#!/usr/bin/env python3
"""
Mermaid diagram generator module for Backstage components and systems.
This module contains all the Mermaid diagram generation logic separated from MCP server logic.
"""

import logging
import json
from api_client import fetch_backstage_component_relations, fetch_backstage_systems

logger = logging.getLogger("agentics-mcp.mermaid_generator")


async def generate_component_dependency_diagram(component_name: str) -> str:
    """Generate a Mermaid diagram for a component and all its dependencies.
    
    Args:
        component_name: The name of the component to generate diagram for
        
    Returns:
        Mermaid diagram as string showing component dependencies, or error message if failed
    """
    try:
        logger.info(f"Generating component dependency diagram for: {component_name}")
        
        # Get the component relations
        component_relations = await fetch_backstage_component_relations(component_name)
        
        # Parse the relations JSON
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
        
        # Add all entities to diagram - using only names, no descriptions
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
        logger.info(f"Successfully generated component dependency diagram for: {component_name}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate component dependency diagram for {component_name}: {e}", exc_info=True)
        return json.dumps({"error": "Diagram generation error", "message": f"Failed to generate diagram: {str(e)}", "component": component_name}, indent=2)


async def generate_systems_overview_diagram() -> str:
    """Generate a Mermaid diagram showing all systems with team ownership boundaries.
    
    Returns:
        Mermaid diagram as string showing all systems with team boundaries, or error message if failed
    """
    try:
        logger.info("Generating systems overview diagram")
        
        # Get all systems data
        systems_data = await fetch_backstage_systems()
        
        # Parse the systems JSON
        try:
            systems_info = json.loads(systems_data)
        except json.JSONDecodeError:
            # If it's an error message, return it
            return systems_data
        
        # Start building the Mermaid diagram
        mermaid_lines = [
            "```mermaid",
            "graph TD",
            "    %% All Systems Overview with Team Ownership",
            ""
        ]
        
        # Track all entities
        all_components = set()
        all_apis = set()
        teams = set()
        
        # Process each system
        for system in systems_info.get("systems", []):
            system_name = system.get("name", "")
            components = system.get("components", [])
            owners = system.get("owners", [])
            
            # Add system as subgraph with team boundaries
            mermaid_lines.append(f"    subgraph \"{system_name.title()} System\"")
            
            # Group components by team
            teams_in_system = {}
            for component in components:
                all_components.add(component)
                
                # Get component details to find its owner
                component_relations = await fetch_backstage_component_relations(component)
                try:
                    relations_data = json.loads(component_relations)
                    component_owner = None
                    for relation in relations_data:
                        if relation.get("type") == "ownedBy":
                            target_ref = relation.get("targetRef", "")
                            if target_ref.startswith("group:default/"):
                                component_owner = target_ref.replace("group:default/", "")
                                teams.add(component_owner)
                                break
                    
                    if component_owner:
                        if component_owner not in teams_in_system:
                            teams_in_system[component_owner] = []
                        teams_in_system[component_owner].append(component)
                    else:
                        # Fallback - use system owners
                        for owner in owners:
                            clean_owner = owner.replace("group:default/", "").replace("team-", "")
                            teams.add(clean_owner)
                            if clean_owner not in teams_in_system:
                                teams_in_system[clean_owner] = []
                            teams_in_system[clean_owner].append(component)
                            break
                except:
                    # If we can't get relations, use system owners as fallback
                    for owner in owners:
                        clean_owner = owner.replace("group:default/", "").replace("team-", "")
                        teams.add(clean_owner)
                        if clean_owner not in teams_in_system:
                            teams_in_system[clean_owner] = []
                        teams_in_system[clean_owner].append(component)
                        break
            
            # Add team subgraphs within system
            for team, team_components in teams_in_system.items():
                mermaid_lines.append(f"        subgraph \"{team}\"")
                for component in team_components:
                    comp_var = component.replace('-', '_').upper()
                    mermaid_lines.append(f"            {comp_var}[{component}]")
                mermaid_lines.append("        end")
            
            mermaid_lines.append("    end")
            mermaid_lines.append("")
        
        # Add API relationships between components
        mermaid_lines.append("    %% API Dependencies")
        for component in all_components:
            try:
                component_relations = await fetch_backstage_component_relations(component)
                relations_data = json.loads(component_relations)
                comp_var = component.replace('-', '_').upper()
                
                for relation in relations_data:
                    rel_type = relation.get("type", "")
                    target_ref = relation.get("targetRef", "")
                    
                    if rel_type == "consumesApi" and target_ref.startswith("api:default/"):
                        api_name = target_ref.replace("api:default/", "")
                        api_var = api_name.replace('-', '_').upper()
                        all_apis.add(api_name)
                        mermaid_lines.append(f"    {comp_var} -->|consumes| {api_var}[{api_name}]")
                    elif rel_type == "providesApi" and target_ref.startswith("api:default/"):
                        api_name = target_ref.replace("api:default/", "")
                        api_var = api_name.replace('-', '_').upper()
                        all_apis.add(api_name)
                        mermaid_lines.append(f"    {comp_var} -->|provides| {api_var}[{api_name}]")
                    elif rel_type == "dependsOn" and target_ref.startswith("component:default/"):
                        dep_component = target_ref.replace("component:default/", "")
                        dep_var = dep_component.replace('-', '_').upper()
                        mermaid_lines.append(f"    {comp_var} -.->|depends on| {dep_var}")
            except:
                continue
        
        mermaid_lines.append("")
        
        # Add styling
        mermaid_lines.extend([
            "    %% Styling with good contrast",
            "    classDef service fill:#2196F3,stroke:#1976D2,stroke-width:2px,color:#ffffff",
            "    classDef api fill:#FF9800,stroke:#F57C00,stroke-width:2px,color:#000000",
            "    classDef website fill:#9C27B0,stroke:#7B1FA2,stroke-width:2px,color:#ffffff",
            ""
        ])
        
        # Classify components (we'll assume services unless we know otherwise)
        component_vars = [comp.replace('-', '_').upper() for comp in all_components]
        if component_vars:
            # Separate frontend from services
            frontend_vars = [var for var in component_vars if 'FRONTEND' in var]
            service_vars = [var for var in component_vars if var not in frontend_vars]
            
            if service_vars:
                mermaid_lines.append(f"    class {','.join(service_vars)} service")
            if frontend_vars:
                mermaid_lines.append(f"    class {','.join(frontend_vars)} website")
        
        # Classify APIs
        api_vars = [api.replace('-', '_').upper() for api in all_apis]
        if api_vars:
            mermaid_lines.append(f"    class {','.join(api_vars)} api")
        
        mermaid_lines.append("```")
        
        result = "\n".join(mermaid_lines)
        logger.info("Successfully generated systems overview diagram")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate systems overview diagram: {e}", exc_info=True)
        return json.dumps({"error": "Diagram generation error", "message": f"Failed to generate systems overview: {str(e)}"}, indent=2)
