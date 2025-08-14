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


async def generate_api_migration_plan_internal(from_api: str, to_api: str, base_url: str = None) -> str:
    """Generate a detailed migration plan from one API version to another with Python code examples.
    
    Args:
        from_api: The name of the source API to migrate from
        to_api: The name of the target API to migrate to
        base_url: Optional base URL override for Backstage API
        
    Returns:
        Detailed migration plan with Python code examples as JSON string, or error message if failed
    """
    try:
        logger.info(f"Generating API migration plan: {from_api} -> {to_api}")
        
        # Fetch both API entities
        from_api_data = await fetch_backstage_api_entity(from_api)
        to_api_data = await fetch_backstage_api_entity(to_api)
        
        # Parse API data
        try:
            from_api_info = json.loads(from_api_data)
            to_api_info = json.loads(to_api_data)
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": "API parsing error",
                "message": f"Failed to parse API data: {str(e)}",
                "from_api": from_api,
                "to_api": to_api
            }, indent=2)
        
        # Check if APIs exist and have proper structure
        if "error" in from_api_info:
            return json.dumps({
                "error": "Source API not found",
                "message": f"Could not find source API '{from_api}' in Backstage catalog. Please verify the API name.",
                "from_api": from_api,
                "to_api": to_api
            }, indent=2)
        
        if "error" in to_api_info:
            return json.dumps({
                "error": "Target API not found", 
                "message": f"Could not find target API '{to_api}' in Backstage catalog. Please verify the API name.",
                "from_api": from_api,
                "to_api": to_api
            }, indent=2)
        
        # Validate that both APIs have the same provider (critical for migration validity)
        from_relations = from_api_info.get("relations", [])
        to_relations = to_api_info.get("relations", [])
        
        from_provider = None
        to_provider = None
        
        for relation in from_relations:
            if relation.get("type") == "apiProvidedBy":
                from_provider = relation.get("targetRef", "").replace("component:default/", "")
                break
        
        for relation in to_relations:
            if relation.get("type") == "apiProvidedBy":
                to_provider = relation.get("targetRef", "").replace("component:default/", "")
                break
        
        # Strict validation: Both APIs must have the same provider
        if not from_provider or not to_provider:
            return json.dumps({
                "error": "Missing API provider relations",
                "message": "Both APIs must have 'apiProvidedBy' relations defined in Backstage. Please ask the architects to ensure proper relations are established before attempting migration.",
                "from_api": from_api,
                "to_api": to_api,
                "from_provider": from_provider,
                "to_provider": to_provider,
                "recommendation": "Contact the system architects to establish proper API provider relations in Backstage catalog."
            }, indent=2)
        
        if from_provider != to_provider:
            return json.dumps({
                "error": "API provider mismatch",
                "message": f"Migration not allowed: APIs are provided by different services. Source API '{from_api}' is provided by '{from_provider}' while target API '{to_api}' is provided by '{to_provider}'. Please ask the architects to verify this is a valid migration path.",
                "from_api": from_api,
                "to_api": to_api,
                "from_provider": from_provider,
                "to_provider": to_provider,
                "recommendation": "Contact the system architects to confirm this cross-service API migration is intentional and properly designed."
            }, indent=2)
        
        # Extract API specifications
        from_spec = from_api_info.get("spec", {})
        to_spec = to_api_info.get("spec", {})
        
        from_definition = from_spec.get("definition", "")
        to_definition = to_spec.get("definition", "")
        
        # Parse OpenAPI definitions
        from_openapi = parse_openapi_definition(from_definition)
        to_openapi = parse_openapi_definition(to_definition)
        
        if not from_openapi or not to_openapi:
            return json.dumps({
                "error": "OpenAPI parsing error",
                "message": "Could not parse OpenAPI definitions from one or both APIs. Migration analysis requires valid OpenAPI specifications.",
                "from_api": from_api,
                "to_api": to_api
            }, indent=2)
        
        # Generate comprehensive migration analysis
        migration_analysis = analyze_api_migration(from_openapi, to_openapi, from_api, to_api)
        
        # Find consumers of the source API
        consumers = []
        for relation in from_relations:
            if relation.get("type") == "apiConsumedBy":
                consumer = relation.get("targetRef", "").replace("component:default/", "")
                if consumer:
                    consumers.append(consumer)
        
        # Generate Markdown migration guide
        markdown_guide = generate_markdown_migration_guide(
            from_api, to_api, from_provider, consumers, 
            from_openapi, to_openapi, from_spec, to_spec, 
            migration_analysis
        )
        
        logger.info(f"Successfully generated migration plan: {from_api} -> {to_api}")
        return markdown_guide
        
    except Exception as e:
        logger.error(f"Failed to generate migration plan {from_api} -> {to_api}: {e}", exc_info=True)
        return json.dumps({
            "error": "Migration plan generation error",
            "message": f"Failed to generate migration plan: {str(e)}",
            "from_api": from_api,
            "to_api": to_api
        }, indent=2)


def parse_openapi_definition(definition: str) -> dict:
    """Parse OpenAPI definition from YAML or JSON string.
    
    Args:
        definition: OpenAPI definition as YAML or JSON string
        
    Returns:
        Parsed OpenAPI specification as dictionary, or empty dict if parsing fails
    """
    try:
        import yaml
        # Try YAML first (most common for OpenAPI)
        return yaml.safe_load(definition)
    except:
        try:
            # Fallback to JSON
            return json.loads(definition)
        except:
            logger.warning("Failed to parse OpenAPI definition as YAML or JSON")
            return {}


def analyze_api_migration(from_openapi: dict, to_openapi: dict, from_api: str, to_api: str) -> dict:
    """Analyze the migration between two OpenAPI specifications.
    
    Args:
        from_openapi: Source API OpenAPI specification
        to_openapi: Target API OpenAPI specification
        from_api: Source API name
        to_api: Target API name
        
    Returns:
        Comprehensive migration analysis with breaking changes, examples, and recommendations
    """
    analysis = {
        "complexity": "medium",
        "estimated_effort": "2-4 hours",
        "breaking_changes": [],
        "new_features": [],
        "removed_features": [],
        "migration_steps": [],
        "python_examples": {},
        "testing_recommendations": [],
        "rollback_strategy": {}
    }
    
    from_paths = from_openapi.get("paths", {})
    to_paths = to_openapi.get("paths", {})
    
    from_info = from_openapi.get("info", {})
    to_info = to_openapi.get("info", {})
    
    # Analyze endpoint changes
    from_endpoints = set(from_paths.keys())
    to_endpoints = set(to_paths.keys())
    
    removed_endpoints = from_endpoints - to_endpoints
    new_endpoints = to_endpoints - from_endpoints
    common_endpoints = from_endpoints & to_endpoints
    
    # Track breaking changes
    if removed_endpoints:
        for endpoint in removed_endpoints:
            analysis["breaking_changes"].append({
                "type": "endpoint_removed",
                "endpoint": endpoint,
                "impact": "high",
                "description": f"Endpoint {endpoint} has been removed and is no longer available"
            })
            analysis["removed_features"].append(f"Endpoint: {endpoint}")
    
    if new_endpoints:
        for endpoint in new_endpoints:
            analysis["new_features"].append(f"New endpoint: {endpoint}")
    
    # Analyze common endpoints for changes
    for endpoint in common_endpoints:
        from_endpoint = from_paths[endpoint]
        to_endpoint = to_paths[endpoint]
        
        # Check for method changes
        from_methods = set(from_endpoint.keys())
        to_methods = set(to_endpoint.keys())
        
        removed_methods = from_methods - to_methods
        new_methods = to_methods - from_methods
        
        if removed_methods:
            for method in removed_methods:
                analysis["breaking_changes"].append({
                    "type": "method_removed",
                    "endpoint": endpoint,
                    "method": method.upper(),
                    "impact": "high",
                    "description": f"HTTP method {method.upper()} removed from {endpoint}"
                })
        
        # Analyze request/response schema changes for common methods
        common_methods = from_methods & to_methods
        for method in common_methods:
            if method in ["get", "post", "put", "patch", "delete"]:
                method_changes = analyze_method_changes(
                    from_endpoint.get(method, {}), 
                    to_endpoint.get(method, {}), 
                    endpoint, 
                    method
                )
                analysis["breaking_changes"].extend(method_changes["breaking_changes"])
                analysis["new_features"].extend(method_changes["new_features"])
    
    # Generate migration complexity assessment
    breaking_change_count = len(analysis["breaking_changes"])
    if breaking_change_count == 0:
        analysis["complexity"] = "low"
        analysis["estimated_effort"] = "1-2 hours"
    elif breaking_change_count <= 3:
        analysis["complexity"] = "medium"
        analysis["estimated_effort"] = "2-4 hours"
    else:
        analysis["complexity"] = "high"
        analysis["estimated_effort"] = "4-8 hours"
    
    # Generate migration steps
    analysis["migration_steps"] = generate_migration_steps(from_openapi, to_openapi, analysis)
    
    # Generate Python code examples
    analysis["python_examples"] = generate_python_migration_examples(from_openapi, to_openapi, from_api, to_api)
    
    # Generate testing recommendations
    analysis["testing_recommendations"] = generate_testing_recommendations(analysis)
    
    # Generate rollback strategy
    analysis["rollback_strategy"] = generate_rollback_strategy(from_api, to_api, analysis)
    
    return analysis


def analyze_method_changes(from_method: dict, to_method: dict, endpoint: str, method: str) -> dict:
    """Analyze changes in a specific HTTP method between API versions."""
    changes = {
        "breaking_changes": [],
        "new_features": []
    }
    
    # Check request body changes
    from_request_body = from_method.get("requestBody", {})
    to_request_body = to_method.get("requestBody", {})
    
    # Check if request body became required
    if not from_request_body.get("required", False) and to_request_body.get("required", False):
        changes["breaking_changes"].append({
            "type": "request_body_required",
            "endpoint": endpoint,
            "method": method.upper(),
            "impact": "medium",
            "description": f"Request body is now required for {method.upper()} {endpoint}"
        })
    
    # Check parameter changes
    from_params = from_method.get("parameters", [])
    to_params = to_method.get("parameters", [])
    
    from_param_names = {p.get("name") for p in from_params if p.get("name")}
    to_param_names = {p.get("name") for p in to_params if p.get("name")}
    
    removed_params = from_param_names - to_param_names
    new_params = to_param_names - from_param_names
    
    for param in removed_params:
        changes["breaking_changes"].append({
            "type": "parameter_removed",
            "endpoint": endpoint,
            "method": method.upper(),
            "parameter": param,
            "impact": "medium",
            "description": f"Parameter '{param}' removed from {method.upper()} {endpoint}"
        })
    
    for param in new_params:
        # Check if new parameter is required
        param_info = next((p for p in to_params if p.get("name") == param), {})
        if param_info.get("required", False):
            changes["breaking_changes"].append({
                "type": "required_parameter_added",
                "endpoint": endpoint,
                "method": method.upper(),
                "parameter": param,
                "impact": "high",
                "description": f"New required parameter '{param}' added to {method.upper()} {endpoint}"
            })
        else:
            changes["new_features"].append(f"New optional parameter '{param}' in {method.upper()} {endpoint}")
    
    return changes


def generate_migration_steps(from_openapi: dict, to_openapi: dict, analysis: dict) -> list:
    """Generate step-by-step migration instructions."""
    steps = [
        {
            "step": 1,
            "title": "Review Breaking Changes",
            "description": "Carefully review all breaking changes identified in this migration plan",
            "action": "Analyze the impact of each breaking change on your application"
        },
        {
            "step": 2,
            "title": "Update API Client Configuration",
            "description": "Update your API client to point to the new API version",
            "action": "Change base URL, API version, and any authentication requirements"
        },
        {
            "step": 3,
            "title": "Update Request/Response Handling",
            "description": "Modify your code to handle changes in request and response formats",
            "action": "Update data structures, field names, and validation logic"
        },
        {
            "step": 4,
            "title": "Implement Error Handling",
            "description": "Update error handling for new error codes and response formats",
            "action": "Test error scenarios and update exception handling"
        },
        {
            "step": 5,
            "title": "Test Migration",
            "description": "Thoroughly test the migration with comprehensive test cases",
            "action": "Run unit tests, integration tests, and manual testing"
        },
        {
            "step": 6,
            "title": "Deploy and Monitor",
            "description": "Deploy the changes and monitor for any issues",
            "action": "Deploy to staging first, then production with careful monitoring"
        }
    ]
    
    # Add specific steps based on breaking changes
    if any(change["type"] == "endpoint_removed" for change in analysis["breaking_changes"]):
        steps.insert(2, {
            "step": "2a",
            "title": "Handle Removed Endpoints",
            "description": "Update code that calls removed endpoints",
            "action": "Find alternative endpoints or remove functionality that depends on removed endpoints"
        })
    
    return steps


def generate_python_migration_examples(from_openapi: dict, to_openapi: dict, from_api: str, to_api: str) -> dict:
    """Generate Python code examples for the migration."""
    examples = {}
    
    from_info = from_openapi.get("info", {})
    to_info = to_openapi.get("info", {})
    
    from_paths = from_openapi.get("paths", {})
    to_paths = to_openapi.get("paths", {})
    
    # Generate basic client setup example
    examples["client_setup"] = {
        "description": "Update your API client configuration",
        "before": f'''import requests

# Old API client setup
class {from_api.replace("-", "_").title()}Client:
    def __init__(self):
        self.base_url = "http://localhost:4010"  # Old API URL
        self.session = requests.Session()
        
    def create_payment(self, amount_cents, currency):
        response = self.session.post(
            f"{{self.base_url}}/payments",
            json={{
                "amountCents": amount_cents,
                "currency": currency
            }}
        )
        return response.json()''',
        "after": f'''import requests
import uuid

# New API client setup
class {to_api.replace("-", "_").title()}Client:
    def __init__(self):
        self.base_url = "http://localhost:4011"  # New API URL
        self.session = requests.Session()
        
    def create_payment(self, amount, currency):
        response = self.session.post(
            f"{{self.base_url}}/v2/payments",
            headers={{
                "Idempotency-Key": str(uuid.uuid4())  # Required for v2
            }},
            json={{
                "amount": amount,  # Now decimal format
                "currency": currency
            }}
        )
        return response.json()'''
    }
    
    # Generate specific endpoint migration examples
    if "/payments" in from_paths and "/v2/payments" in to_paths:
        examples["create_payment"] = {
            "description": "Migrate payment creation from v1 to v2",
            "before": '''# V1 API - Create payment with cents
response = client.create_payment(
    amount_cents=1299,  # $12.99 in cents
    currency="USD"
)

# V1 Response format
payment_id = response["id"]
status = response["status"]
amount_cents = response["amountCents"]''',
            "after": '''# V2 API - Create payment with decimal amount
response = client.create_payment(
    amount=12.99,  # Direct decimal amount
    currency="USD"
)

# V2 Response format (field names changed)
payment_id = response["paymentId"]  # Changed from "id"
state = response["state"]  # Changed from "status"
amount = response["amount"]  # Now decimal format'''
        }
        
        examples["get_payment"] = {
            "description": "Migrate payment retrieval from v1 to v2",
            "before": '''# V1 API - Get payment
response = requests.get(f"http://localhost:4010/payments/{payment_id}")
payment = response.json()

# V1 field access
payment_status = payment["status"]
amount_in_cents = payment["amountCents"]
amount_in_dollars = amount_in_cents / 100  # Manual conversion''',
            "after": '''# V2 API - Get payment
response = requests.get(f"http://localhost:4011/v2/payments/{payment_id}")
payment = response.json()

# V2 field access (updated field names)
payment_state = payment["state"]  # Changed from "status"
amount = payment["amount"]  # Already in decimal format'''
        }
    
    # Generate error handling example
    examples["error_handling"] = {
        "description": "Update error handling for the new API version",
        "before": '''# V1 Error handling
try:
    response = client.create_payment(1299, "USD")
    if response.get("status") == "failed":
        print(f"Payment failed: {response.get('id')}")
except requests.exceptions.RequestException as e:
    print(f"API error: {e}")''',
        "after": '''# V2 Error handling (updated field names and states)
try:
    response = client.create_payment(12.99, "USD")
    if response.get("state") == "failed":  # Changed from "status"
        print(f"Payment failed: {response.get('paymentId')}")  # Changed from "id"
except requests.exceptions.RequestException as e:
    print(f"API error: {e}")'''
    }
    
    return examples


def generate_testing_recommendations(analysis: dict) -> list:
    """Generate testing recommendations for the migration."""
    recommendations = [
        {
            "category": "Unit Tests",
            "description": "Test individual API client methods",
            "tests": [
                "Test successful payment creation with new format",
                "Test payment retrieval with updated field names",
                "Test error handling with new response format",
                "Test idempotency key generation and usage"
            ]
        },
        {
            "category": "Integration Tests",
            "description": "Test end-to-end workflows",
            "tests": [
                "Test complete payment flow from creation to completion",
                "Test error scenarios and recovery",
                "Test concurrent requests with idempotency",
                "Test backward compatibility during transition period"
            ]
        },
        {
            "category": "Performance Tests",
            "description": "Ensure performance is maintained",
            "tests": [
                "Compare response times between v1 and v2",
                "Test with high load to ensure stability",
                "Monitor memory usage and resource consumption"
            ]
        }
    ]
    
    # Add specific tests based on breaking changes
    if analysis["breaking_changes"]:
        recommendations.append({
            "category": "Breaking Change Tests",
            "description": "Specific tests for identified breaking changes",
            "tests": [f"Test handling of: {change['description']}" for change in analysis["breaking_changes"]]
        })
    
    return recommendations


def generate_markdown_migration_guide(from_api: str, to_api: str, provider_service: str, consumers: list, 
                                     from_openapi: dict, to_openapi: dict, from_spec: dict, to_spec: dict, 
                                     migration_analysis: dict) -> str:
    """Generate a human-readable Markdown migration guide.
    
    Args:
        from_api: Source API name
        to_api: Target API name
        provider_service: Service that provides both APIs
        consumers: List of services consuming the source API
        from_openapi: Source API OpenAPI specification
        to_openapi: Target API OpenAPI specification
        from_spec: Source API Backstage spec
        to_spec: Target API Backstage spec
        migration_analysis: Analysis results from analyze_api_migration
        
    Returns:
        Formatted Markdown migration guide
    """
    from datetime import datetime
    
    # Get API version info
    from_version = from_openapi.get("info", {}).get("version", "unknown")
    to_version = to_openapi.get("info", {}).get("version", "unknown")
    from_description = from_openapi.get("info", {}).get("description", "")
    to_description = to_openapi.get("info", {}).get("description", "")
    
    markdown_lines = [
        f"# API Migration Guide: {from_api} → {to_api}",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Migration Complexity:** {migration_analysis['complexity'].upper()}",
        f"**Estimated Effort:** {migration_analysis['estimated_effort']}",
        f"**Breaking Changes:** {len(migration_analysis['breaking_changes'])}",
        "",
        "## 📋 Migration Summary",
        "",
        f"This guide provides step-by-step instructions for migrating from `{from_api}` to `{to_api}`.",
        "",
        f"- **Source API:** `{from_api}` (v{from_version}) - {from_spec.get('lifecycle', 'unknown')}",
        f"- **Target API:** `{to_api}` (v{to_version}) - {to_spec.get('lifecycle', 'unknown')}",
        f"- **Provider Service:** `{provider_service}`",
        f"- **Affected Consumers:** {', '.join([f'`{c}`' for c in consumers]) if consumers else 'None'}",
        "",
        "### ✅ Validation Status",
        "",
        "- ✅ **Backstage Relations Verified:** Both APIs have proper `apiProvidedBy` relations",
        f"- ✅ **Same Provider Confirmed:** Both APIs are provided by `{provider_service}`",
        "- ✅ **Migration Path Valid:** This is a safe migration between API versions",
        "",
    ]
    
    # Add API comparison section
    markdown_lines.extend([
        "## 🔄 API Comparison",
        "",
        "| Aspect | Source API | Target API |",
        "|--------|------------|------------|",
        f"| **Name** | `{from_api}` | `{to_api}` |",
        f"| **Version** | {from_version} | {to_version} |",
        f"| **Lifecycle** | {from_spec.get('lifecycle', 'unknown')} | {to_spec.get('lifecycle', 'unknown')} |",
        f"| **Description** | {from_description} | {to_description} |",
        "",
    ])
    
    # Add breaking changes section
    if migration_analysis["breaking_changes"]:
        markdown_lines.extend([
            "## ⚠️ Breaking Changes",
            "",
            "The following breaking changes require code updates:",
            "",
        ])
        
        for i, change in enumerate(migration_analysis["breaking_changes"], 1):
            impact_emoji = "🔴" if change["impact"] == "high" else "🟡" if change["impact"] == "medium" else "🟢"
            markdown_lines.extend([
                f"### {i}. {change['description']}",
                "",
                f"- **Type:** {change['type'].replace('_', ' ').title()}",
                f"- **Impact:** {impact_emoji} {change['impact'].title()}",
                f"- **Endpoint:** `{change.get('endpoint', 'N/A')}`",
                "",
            ])
    else:
        markdown_lines.extend([
            "## ✅ No Breaking Changes",
            "",
            "This migration has no breaking changes and should be straightforward to implement.",
            "",
        ])
    
    # Add new features section
    if migration_analysis["new_features"]:
        markdown_lines.extend([
            "## 🆕 New Features",
            "",
            "The target API introduces the following new features:",
            "",
        ])
        
        for feature in migration_analysis["new_features"]:
            markdown_lines.append(f"- {feature}")
        
        markdown_lines.append("")
    
    # Add removed features section
    if migration_analysis["removed_features"]:
        markdown_lines.extend([
            "## 🗑️ Removed Features",
            "",
            "⚠️ **The following features have been removed and are no longer available:**",
            "",
        ])
        
        for feature in migration_analysis["removed_features"]:
            markdown_lines.append(f"- ❌ {feature}")
        
        markdown_lines.append("")
    
    # Add migration steps
    markdown_lines.extend([
        "## 📝 Migration Steps",
        "",
        "Follow these steps to complete the migration:",
        "",
    ])
    
    for step in migration_analysis["migration_steps"]:
        step_num = step["step"]
        markdown_lines.extend([
            f"### Step {step_num}: {step['title']}",
            "",
            f"**Description:** {step['description']}",
            "",
            f"**Action:** {step['action']}",
            "",
        ])
    
    # Add Python code examples
    markdown_lines.extend([
        "## 🐍 Python Code Examples",
        "",
        "Here are specific code examples to help with the migration:",
        "",
    ])
    
    for example_name, example_data in migration_analysis["python_examples"].items():
        markdown_lines.extend([
            f"### {example_name.replace('_', ' ').title()}",
            "",
            f"**{example_data['description']}**",
            "",
            "#### Before (Old API):",
            "",
            "```python",
            example_data["before"],
            "```",
            "",
            "#### After (New API):",
            "",
            "```python",
            example_data["after"],
            "```",
            "",
        ])
    
    # Add testing recommendations
    markdown_lines.extend([
        "## 🧪 Testing Recommendations",
        "",
        "Comprehensive testing is crucial for a successful migration:",
        "",
    ])
    
    for recommendation in migration_analysis["testing_recommendations"]:
        markdown_lines.extend([
            f"### {recommendation['category']}",
            "",
            f"**{recommendation['description']}**",
            "",
        ])
        
        for test in recommendation["tests"]:
            markdown_lines.append(f"- [ ] {test}")
        
        markdown_lines.append("")
    
    # Add rollback strategy
    rollback = migration_analysis["rollback_strategy"]
    markdown_lines.extend([
        "## 🔄 Rollback Strategy",
        "",
        "Be prepared to rollback if issues arise during or after migration.",
        "",
        "### Preparation",
        "",
    ])
    
    for prep in rollback["preparation"]:
        markdown_lines.append(f"- [ ] {prep}")
    
    markdown_lines.extend([
        "",
        "### Rollback Triggers",
        "",
        "Consider rolling back if you encounter:",
        "",
    ])
    
    for trigger in rollback["rollback_triggers"]:
        markdown_lines.append(f"- 🚨 {trigger}")
    
    markdown_lines.extend([
        "",
        "### Rollback Steps",
        "",
        "If rollback is necessary, follow these steps:",
        "",
    ])
    
    for step in rollback["rollback_steps"]:
        markdown_lines.extend([
            f"**{step['step']}. {step['action']}**",
            "",
            f"```bash",
            f"{step['command']}",
            f"```",
            "",
        ])
    
    markdown_lines.extend([
        "### Monitoring",
        "",
        "Set up monitoring for:",
        "",
    ])
    
    for monitor in rollback["monitoring"]:
        markdown_lines.append(f"- 📊 {monitor}")
    
    markdown_lines.extend([
        "",
        "## 🎯 Next Steps",
        "",
        f"1. **Review this migration guide** thoroughly with your team",
        f"2. **Coordinate with `{provider_service}` team** (API provider) for any questions",
        f"3. **Plan the migration** during a maintenance window",
        f"4. **Test extensively** in staging environment first",
        f"5. **Monitor closely** after production deployment",
        "",
        "---",
        "",
        f"*This migration guide was automatically generated by analyzing the Backstage catalog and OpenAPI specifications. For questions about the migration process, contact the system architects or the `{provider_service}` team.*",
    ])
    
    return "\n".join(markdown_lines)


def generate_testing_recommendations(analysis: dict) -> list:
    """Generate testing recommendations for the migration."""
    recommendations = [
        {
            "category": "Unit Tests",
            "description": "Test individual API client methods",
            "tests": [
                "Test successful payment creation with new format",
                "Test payment retrieval with updated field names",
                "Test error handling with new response format",
                "Test idempotency key generation and usage"
            ]
        },
        {
            "category": "Integration Tests",
            "description": "Test end-to-end workflows",
            "tests": [
                "Test complete payment flow from creation to completion",
                "Test error scenarios and recovery",
                "Test concurrent requests with idempotency",
                "Test backward compatibility during transition period"
            ]
        },
        {
            "category": "Performance Tests",
            "description": "Ensure performance is maintained",
            "tests": [
                "Compare response times between v1 and v2",
                "Test with high load to ensure stability",
                "Monitor memory usage and resource consumption"
            ]
        }
    ]
    
    # Add specific tests based on breaking changes
    if analysis["breaking_changes"]:
        recommendations.append({
            "category": "Breaking Change Tests",
            "description": "Specific tests for identified breaking changes",
            "tests": [f"Test handling of: {change['description']}" for change in analysis["breaking_changes"]]
        })
    
    return recommendations


def generate_rollback_strategy(from_api: str, to_api: str, analysis: dict) -> dict:
    """Generate a rollback strategy for the migration."""
    return {
        "preparation": [
            "Keep the old API client code in version control",
            "Maintain feature flags to switch between API versions",
            "Document all configuration changes made during migration",
            "Create database backups if data format changes are involved"
        ],
        "rollback_triggers": [
            "Increased error rates after deployment",
            "Performance degradation compared to previous version",
            "Critical functionality failures",
            "User-reported issues that cannot be quickly resolved"
        ],
        "rollback_steps": [
            {
                "step": 1,
                "action": "Immediately switch traffic back to old API version",
                "command": "Update configuration to point to old API endpoints"
            },
            {
                "step": 2,
                "action": "Revert code changes",
                "command": "git revert <migration-commit-hash>"
            },
            {
                "step": 3,
                "action": "Redeploy previous version",
                "command": "Deploy the reverted code to production"
            },
            {
                "step": 4,
                "action": "Verify system stability",
                "command": "Run health checks and monitor system metrics"
            },
            {
                "step": 5,
                "action": "Analyze failure and plan fixes",
                "command": "Review logs and plan corrective actions"
            }
        ],
        "monitoring": [
            "Set up alerts for API error rates",
            "Monitor response times and throughput",
            "Track business metrics affected by the API",
            "Set up dashboards for real-time visibility"
        ]
    }
