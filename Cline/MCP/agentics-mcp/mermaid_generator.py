#!/usr/bin/env python3
"""
Mermaid diagram generator module for Backstage components and systems.
This module contains all the Mermaid diagram generation logic separated from MCP server logic.
"""

import logging
import json
from api_client import fetch_backstage_component_relations, fetch_backstage_systems, fetch_backstage_api_entity, fetch_deprecated_entities

logger = logging.getLogger("agentics-mcp.mermaid_generator")


async def get_deprecated_entities_set() -> set:
    """Get a set of all deprecated entity names for efficient lookup.
    
    Returns:
        Set of deprecated entity names
    """
    try:
        deprecated_data = await fetch_deprecated_entities()
        deprecated_info = json.loads(deprecated_data)
        
        deprecated_names = set()
        for entity in deprecated_info.get("deprecated_entities", []):
            deprecated_names.add(entity.get("name", ""))
        
        logger.info(f"Found {len(deprecated_names)} deprecated entities")
        return deprecated_names
    except Exception as e:
        logger.warning(f"Failed to fetch deprecated entities: {e}")
        return set()


async def check_api_lifecycle_batch(api_names: list) -> dict:
    """Check lifecycle status for multiple APIs efficiently.
    
    Args:
        api_names: List of API names to check
        
    Returns:
        Dictionary mapping API names to their lifecycle status
    """
    lifecycle_map = {}
    for api_name in api_names:
        try:
            api_data = await fetch_backstage_api_entity(api_name)
            api_info = json.loads(api_data)
            lifecycle = api_info.get("spec", {}).get("lifecycle", "production")
            lifecycle_map[api_name] = lifecycle
        except:
            lifecycle_map[api_name] = "production"  # Default to production if we can't determine
    return lifecycle_map


async def generate_component_dependency_diagram(component_name: str) -> str:
    """Generate a Mermaid diagram for a component and all its dependencies.
    
    Args:
        component_name: The name of the component to generate diagram for
        
    Returns:
        Mermaid diagram as string showing component dependencies, or error message if failed
    """
    try:
        logger.info(f"Generating component dependency diagram for: {component_name}")
        
        # Get deprecated entities for efficient lookup
        deprecated_entities = await get_deprecated_entities_set()
        
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
        ]
        
        # Add main component with deprecated check
        main_comp_var = component_name.replace('-', '_').upper()
        if component_name in deprecated_entities:
            mermaid_lines.append(f"    {main_comp_var}[{component_name}<br/>DEPRECATED]")
        else:
            mermaid_lines.append(f"    {main_comp_var}[{component_name}]")
        
        mermaid_lines.append("")
        
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
        
        # Add all entities to diagram - using only names, with deprecated detection
        for api in apis:
            api_var = api.replace('-', '_').upper()
            # Check if API is deprecated using the efficient lookup
            if api in deprecated_entities:
                mermaid_lines.append(f"    {api_var}[{api}<br/>DEPRECATED]")
            else:
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
            "    classDef deprecated fill:#FF5722,stroke:#D32F2F,stroke-width:3px,color:#ffffff,stroke-dasharray: 5 5",
            ""
        ])
        
        # Classify main component, checking if deprecated
        if component_name in deprecated_entities:
            mermaid_lines.append(f"    class {main_comp_var} deprecated")
        else:
            mermaid_lines.append(f"    class {main_comp_var} service")
        
        # Classify other components as services, separating deprecated ones
        deprecated_component_vars = []
        service_component_vars = []
        
        for comp in components:
            if comp != component_name:  # Skip main component, already handled
                comp_var = comp.replace('-', '_').upper()
                if comp in deprecated_entities:
                    deprecated_component_vars.append(comp_var)
                else:
                    service_component_vars.append(comp_var)
        
        if service_component_vars:
            mermaid_lines.append(f"    class {','.join(service_component_vars)} service")
        
        # Classify APIs, separating deprecated ones
        deprecated_api_vars = []
        non_deprecated_api_vars = []
        
        for api in apis:
            api_var = api.replace('-', '_').upper()
            if api in deprecated_entities:
                deprecated_api_vars.append(api_var)
            else:
                non_deprecated_api_vars.append(api_var)
        
        if non_deprecated_api_vars:
            mermaid_lines.append(f"    class {','.join(non_deprecated_api_vars)} api")
        
        # Classify groups
        group_vars = [group.replace('-', '_').upper() for group in groups]
        if group_vars:
            mermaid_lines.append(f"    class {','.join(group_vars)} group")
        
        # Classify systems
        system_vars = [system.replace('-', '_').upper() for system in systems]
        if system_vars:
            mermaid_lines.append(f"    class {','.join(system_vars)} system")
        
        # Apply deprecated styling
        if deprecated_component_vars:
            mermaid_lines.append(f"    class {','.join(deprecated_component_vars)} deprecated")
        if deprecated_api_vars:
            mermaid_lines.append(f"    class {','.join(deprecated_api_vars)} deprecated")
        
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
        
        # Get deprecated entities for efficient lookup
        deprecated_entities = await get_deprecated_entities_set()
        
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
                    # Check if component is deprecated
                    if component in deprecated_entities:
                        mermaid_lines.append(f"            {comp_var}[{component}<br/>DEPRECATED]")
                    else:
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
                        # Check if API is deprecated
                        if api_name in deprecated_entities:
                            mermaid_lines.append(f"    {comp_var} -->|consumes| {api_var}[{api_name}<br/>DEPRECATED]")
                        else:
                            mermaid_lines.append(f"    {comp_var} -->|consumes| {api_var}[{api_name}]")
                    elif rel_type == "providesApi" and target_ref.startswith("api:default/"):
                        api_name = target_ref.replace("api:default/", "")
                        api_var = api_name.replace('-', '_').upper()
                        all_apis.add(api_name)
                        # Check if API is deprecated
                        if api_name in deprecated_entities:
                            mermaid_lines.append(f"    {comp_var} -->|provides| {api_var}[{api_name}<br/>DEPRECATED]")
                        else:
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
            "    classDef deprecated fill:#FF5722,stroke:#D32F2F,stroke-width:3px,color:#ffffff,stroke-dasharray: 5 5",
            ""
        ])
        
        # Classify components and APIs, separating deprecated ones
        deprecated_component_vars = []
        deprecated_api_vars = []
        
        component_vars = [comp.replace('-', '_').upper() for comp in all_components]
        if component_vars:
            # Separate deprecated from non-deprecated, and frontend from services
            frontend_vars = []
            service_vars = []
            
            for comp in all_components:
                comp_var = comp.replace('-', '_').upper()
                if comp in deprecated_entities:
                    deprecated_component_vars.append(comp_var)
                elif 'FRONTEND' in comp_var:
                    frontend_vars.append(comp_var)
                else:
                    service_vars.append(comp_var)
            
            if service_vars:
                mermaid_lines.append(f"    class {','.join(service_vars)} service")
            if frontend_vars:
                mermaid_lines.append(f"    class {','.join(frontend_vars)} website")
        
        # Classify APIs, separating deprecated ones
        for api in all_apis:
            api_var = api.replace('-', '_').upper()
            if api in deprecated_entities:
                deprecated_api_vars.append(api_var)
        
        non_deprecated_api_vars = [api.replace('-', '_').upper() for api in all_apis if api not in deprecated_entities]
        if non_deprecated_api_vars:
            mermaid_lines.append(f"    class {','.join(non_deprecated_api_vars)} api")
        
        # Apply deprecated styling
        if deprecated_component_vars:
            mermaid_lines.append(f"    class {','.join(deprecated_component_vars)} deprecated")
        if deprecated_api_vars:
            mermaid_lines.append(f"    class {','.join(deprecated_api_vars)} deprecated")
        
        mermaid_lines.append("```")
        
        result = "\n".join(mermaid_lines)
        logger.info("Successfully generated systems overview diagram")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate systems overview diagram: {e}", exc_info=True)
        return json.dumps({"error": "Diagram generation error", "message": f"Failed to generate systems overview: {str(e)}"}, indent=2)


async def generate_single_system_diagram(system_name: str) -> str:
    """Generate a Mermaid diagram for a single system showing its components and relationships.
    
    Args:
        system_name: The name of the system to generate diagram for
        
    Returns:
        Mermaid diagram as string showing single system architecture, or error message if failed
    """
    try:
        logger.info(f"Generating single system diagram for: {system_name}")
        
        # Get deprecated entities for efficient lookup
        deprecated_entities = await get_deprecated_entities_set()
        
        # Import here to avoid circular imports
        from api_client import fetch_backstage_components_by_system
        
        # Get components for the specific system
        components_data = await fetch_backstage_components_by_system(system_name)
        
        # Parse the components JSON
        try:
            system_info = json.loads(components_data)
        except json.JSONDecodeError:
            # If it's an error message, return it
            return components_data
        
        # Start building the Mermaid diagram
        mermaid_lines = [
            "```mermaid",
            "graph TD",
            f"    %% {system_name.title()} System Architecture",
            ""
        ]
        
        # Track entities
        components = []
        apis = set()
        teams = set()
        
        # Process components in the system
        for component in system_info.get("components", []):
            comp_name = component.get("name", "")
            comp_owner = component.get("owner", "")
            comp_type = component.get("type", "service")
            relations = component.get("relations", [])
            
            components.append({
                "name": comp_name,
                "type": comp_type,
                "owner": comp_owner,
                "relations": relations
            })
            
            # Extract team from owner
            if comp_owner:
                clean_owner = comp_owner.replace("group:default/", "").replace("team-", "")
                teams.add(clean_owner)
            
            # Extract APIs from relations
            for relation in relations:
                rel_type = relation.get("type", "")
                target_ref = relation.get("targetRef", "")
                
                if target_ref.startswith("api:default/"):
                    api_name = target_ref.replace("api:default/", "")
                    apis.add(api_name)
        
        # Add system subgraph with team boundaries
        mermaid_lines.append(f"    subgraph \"{system_name.title()} System\"")
        
        # Group components by team
        teams_in_system = {}
        for component in components:
            comp_name = component["name"]
            comp_owner = component["owner"]
            
            # Determine team
            team = None
            if comp_owner:
                team = comp_owner.replace("group:default/", "").replace("team-", "")
            
            if team:
                if team not in teams_in_system:
                    teams_in_system[team] = []
                teams_in_system[team].append(component)
        
        # Add team subgraphs
        for team, team_components in teams_in_system.items():
            mermaid_lines.append(f"        subgraph \"{team}\"")
            for component in team_components:
                comp_name = component["name"]
                comp_var = comp_name.replace('-', '_').upper()
                # Check if component is deprecated
                if comp_name in deprecated_entities:
                    mermaid_lines.append(f"            {comp_var}[{comp_name}<br/>DEPRECATED]")
                else:
                    mermaid_lines.append(f"            {comp_var}[{comp_name}]")
            mermaid_lines.append("        end")
        
        mermaid_lines.append("    end")
        mermaid_lines.append("")
        
        # Add APIs outside the system subgraph
        for api in apis:
            api_var = api.replace('-', '_').upper()
            # Check if API is deprecated
            if api in deprecated_entities:
                mermaid_lines.append(f"    {api_var}[{api}<br/>DEPRECATED]")
            else:
                mermaid_lines.append(f"    {api_var}[{api}]")
        
        mermaid_lines.append("")
        
        # Add relationships
        mermaid_lines.append("    %% Component Relationships")
        for component in components:
            comp_name = component["name"]
            comp_var = comp_name.replace('-', '_').upper()
            relations = component["relations"]
            
            for relation in relations:
                rel_type = relation.get("type", "")
                target_ref = relation.get("targetRef", "")
                
                if rel_type == "consumesApi" and target_ref.startswith("api:default/"):
                    api_name = target_ref.replace("api:default/", "")
                    api_var = api_name.replace('-', '_').upper()
                    mermaid_lines.append(f"    {comp_var} -->|consumes| {api_var}")
                elif rel_type == "providesApi" and target_ref.startswith("api:default/"):
                    api_name = target_ref.replace("api:default/", "")
                    api_var = api_name.replace('-', '_').upper()
                    mermaid_lines.append(f"    {comp_var} -->|provides| {api_var}")
                elif rel_type == "dependsOn" and target_ref.startswith("component:default/"):
                    dep_component = target_ref.replace("component:default/", "")
                    dep_var = dep_component.replace('-', '_').upper()
                    mermaid_lines.append(f"    {comp_var} -.->|depends on| {dep_var}")
        
        mermaid_lines.append("")
        
        # Add styling
        mermaid_lines.extend([
            "    %% Styling with good contrast",
            "    classDef service fill:#2196F3,stroke:#1976D2,stroke-width:2px,color:#ffffff",
            "    classDef api fill:#FF9800,stroke:#F57C00,stroke-width:2px,color:#000000",
            "    classDef website fill:#9C27B0,stroke:#7B1FA2,stroke-width:2px,color:#ffffff",
            "    classDef deprecated fill:#FF5722,stroke:#D32F2F,stroke-width:3px,color:#ffffff,stroke-dasharray: 5 5",
            ""
        ])
        
        # Classify components by type, separating deprecated ones
        service_vars = []
        website_vars = []
        deprecated_component_vars = []
        
        for component in components:
            comp_name = component["name"]
            comp_var = comp_name.replace('-', '_').upper()
            comp_type = component["type"]
            
            if comp_name in deprecated_entities:
                deprecated_component_vars.append(comp_var)
            elif comp_type == "website":
                website_vars.append(comp_var)
            else:
                service_vars.append(comp_var)
        
        if service_vars:
            mermaid_lines.append(f"    class {','.join(service_vars)} service")
        if website_vars:
            mermaid_lines.append(f"    class {','.join(website_vars)} website")
        
        # Classify APIs, separating deprecated ones
        deprecated_api_vars = []
        non_deprecated_api_vars = []
        
        for api in apis:
            api_var = api.replace('-', '_').upper()
            if api in deprecated_entities:
                deprecated_api_vars.append(api_var)
            else:
                non_deprecated_api_vars.append(api_var)
        
        if non_deprecated_api_vars:
            mermaid_lines.append(f"    class {','.join(non_deprecated_api_vars)} api")
        
        # Apply deprecated styling
        if deprecated_component_vars:
            mermaid_lines.append(f"    class {','.join(deprecated_component_vars)} deprecated")
        if deprecated_api_vars:
            mermaid_lines.append(f"    class {','.join(deprecated_api_vars)} deprecated")
        
        mermaid_lines.append("```")
        
        result = "\n".join(mermaid_lines)
        logger.info(f"Successfully generated single system diagram for: {system_name}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate single system diagram for {system_name}: {e}", exc_info=True)
        return json.dumps({"error": "Diagram generation error", "message": f"Failed to generate single system diagram: {str(e)}", "system": system_name}, indent=2)
