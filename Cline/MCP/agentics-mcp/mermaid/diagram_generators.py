#!/usr/bin/env python3
"""
Mermaid diagram generators for Backstage components and systems.
This module contains functions for generating different types of Mermaid diagrams.
"""

import logging
import json
import asyncio
from typing import Set, List, Dict
from .utils import (
    get_deprecated_entities_set, 
    create_mermaid_variable_name, 
    get_mermaid_styling_classes,
    classify_entities_by_type,
    parse_backstage_reference,
    clean_team_name
)

logger = logging.getLogger("agentics-mcp.mermaid.diagram_generators")


async def generate_component_dependency_diagram(component_name: str) -> str:
    """Generate a Mermaid diagram for a component and all its dependencies.
    
    Args:
        component_name: The name of the component to generate diagram for
        
    Returns:
        Mermaid diagram as string showing component dependencies, or error message if failed
    """
    try:
        logger.info(f"Generating component dependency diagram for: {component_name}")
        
        # Import here to avoid circular imports
        from api_client import fetch_backstage_component_relations
        
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
        main_comp_var = create_mermaid_variable_name(component_name)
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
            
            entity_type, entity_name = parse_backstage_reference(target_ref)
            
            if entity_type == "api":
                apis.add(entity_name)
                if rel_type == "consumesApi":
                    consumes_apis.append(entity_name)
                elif rel_type == "providesApi":
                    provides_apis.append(entity_name)
            elif entity_type == "component":
                components.add(entity_name)
                if rel_type == "dependsOn":
                    depends_on_components.append(entity_name)
            elif entity_type == "group":
                groups.add(entity_name)
                if rel_type == "ownedBy":
                    owned_by_groups.append(entity_name)
            elif entity_type == "system":
                systems.add(entity_name)
                if rel_type == "partOf":
                    part_of_systems.append(entity_name)
        
        # Add all entities to diagram - using only names, with deprecated detection
        for api in apis:
            api_var = create_mermaid_variable_name(api)
            # Check if API is deprecated using the efficient lookup
            if api in deprecated_entities:
                mermaid_lines.append(f"    {api_var}[{api}<br/>DEPRECATED]")
            else:
                mermaid_lines.append(f"    {api_var}[{api}]")
        
        for comp in components:
            if comp != component_name:  # Already added
                comp_var = create_mermaid_variable_name(comp)
                mermaid_lines.append(f"    {comp_var}[{comp}]")
        
        for group in groups:
            group_var = create_mermaid_variable_name(group)
            mermaid_lines.append(f"    {group_var}[{group}]")
        
        for system in systems:
            system_var = create_mermaid_variable_name(system)
            mermaid_lines.append(f"    {system_var}[{system}]")
        
        mermaid_lines.append("")
        
        # Add relationships
        for api in consumes_apis:
            api_var = create_mermaid_variable_name(api)
            mermaid_lines.append(f"    {main_comp_var} -->|consumes| {api_var}")
        
        for api in provides_apis:
            api_var = create_mermaid_variable_name(api)
            mermaid_lines.append(f"    {main_comp_var} -->|provides| {api_var}")
        
        for comp in depends_on_components:
            comp_var = create_mermaid_variable_name(comp)
            mermaid_lines.append(f"    {main_comp_var} -.->|depends on| {comp_var}")
        
        for group in owned_by_groups:
            group_var = create_mermaid_variable_name(group)
            mermaid_lines.append(f"    {main_comp_var} -.->|owned by| {group_var}")
        
        for system in part_of_systems:
            system_var = create_mermaid_variable_name(system)
            mermaid_lines.append(f"    {main_comp_var} -.->|part of| {system_var}")
        
        mermaid_lines.append("")
        
        # Add styling
        mermaid_lines.extend(get_mermaid_styling_classes())
        
        # Classify and apply styles
        _apply_component_diagram_styles(mermaid_lines, component_name, components, apis, groups, systems, deprecated_entities)
        
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
        
        # Import here to avoid circular imports
        from api_client import fetch_backstage_systems, fetch_backstage_component_relations
        
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
        
        # Process each system with rate limiting
        for system in systems_info.get("systems", []):
            system_name = system.get("name", "")
            components = system.get("components", [])
            owners = system.get("owners", [])
            
            # Add system as subgraph with team boundaries
            mermaid_lines.append(f"    subgraph \"{system_name.title()} System\"")
            
            # Group components by team with rate limiting
            teams_in_system = {}
            for i, component in enumerate(components):
                all_components.add(component)
                
                # Add rate limiting - small delay between API calls
                if i > 0:
                    await asyncio.sleep(0.1)  # 100ms delay between calls
                
                try:
                    # Get component details to find its owner with timeout
                    component_relations = await asyncio.wait_for(
                        fetch_backstage_component_relations(component), 
                        timeout=5.0  # 5 second timeout
                    )
                    
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
                            clean_owner = clean_team_name(owner)
                            teams.add(clean_owner)
                            if clean_owner not in teams_in_system:
                                teams_in_system[clean_owner] = []
                            teams_in_system[clean_owner].append(component)
                            break
                            
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"Failed to get relations for component {component}: {e}")
                    # If we can't get relations, use system owners as fallback
                    for owner in owners:
                        clean_owner = clean_team_name(owner)
                        teams.add(clean_owner)
                        if clean_owner not in teams_in_system:
                            teams_in_system[clean_owner] = []
                        teams_in_system[clean_owner].append(component)
                        break
            
            # Add team subgraphs within system
            for team, team_components in teams_in_system.items():
                mermaid_lines.append(f"        subgraph \"{team}\"")
                for component in team_components:
                    comp_var = create_mermaid_variable_name(component)
                    # Check if component is deprecated
                    if component in deprecated_entities:
                        mermaid_lines.append(f"            {comp_var}[{component}<br/>DEPRECATED]")
                    else:
                        mermaid_lines.append(f"            {comp_var}[{component}]")
                mermaid_lines.append("        end")
            
            mermaid_lines.append("    end")
            mermaid_lines.append("")
        
        # Add API relationships between components with rate limiting
        mermaid_lines.append("    %% API Dependencies")
        for i, component in enumerate(all_components):
            # Add rate limiting for API relationship calls
            if i > 0:
                await asyncio.sleep(0.1)  # 100ms delay between calls
            
            try:
                # Use timeout for component relations calls
                component_relations = await asyncio.wait_for(
                    fetch_backstage_component_relations(component),
                    timeout=5.0  # 5 second timeout
                )
                relations_data = json.loads(component_relations)
                comp_var = create_mermaid_variable_name(component)
                
                for relation in relations_data:
                    rel_type = relation.get("type", "")
                    target_ref = relation.get("targetRef", "")
                    
                    entity_type, entity_name = parse_backstage_reference(target_ref)
                    
                    if entity_type == "api":
                        api_var = create_mermaid_variable_name(entity_name)
                        all_apis.add(entity_name)
                        
                        if rel_type == "consumesApi":
                            # Check if API is deprecated
                            if entity_name in deprecated_entities:
                                mermaid_lines.append(f"    {comp_var} -->|consumes| {api_var}[{entity_name}<br/>DEPRECATED]")
                            else:
                                mermaid_lines.append(f"    {comp_var} -->|consumes| {api_var}[{entity_name}]")
                        elif rel_type == "providesApi":
                            # Check if API is deprecated
                            if entity_name in deprecated_entities:
                                mermaid_lines.append(f"    {comp_var} -->|provides| {api_var}[{entity_name}<br/>DEPRECATED]")
                            else:
                                mermaid_lines.append(f"    {comp_var} -->|provides| {api_var}[{entity_name}]")
                    elif entity_type == "component":
                        if rel_type == "dependsOn":
                            dep_var = create_mermaid_variable_name(entity_name)
                            mermaid_lines.append(f"    {comp_var} -.->|depends on| {dep_var}")
                            
            except (asyncio.TimeoutError, Exception) as e:
                logger.warning(f"Failed to get API relations for component {component}: {e}")
                continue
        
        mermaid_lines.append("")
        
        # Add styling
        mermaid_lines.extend(get_mermaid_styling_classes())
        
        # Classify and apply styles
        _apply_systems_overview_styles(mermaid_lines, all_components, all_apis, deprecated_entities)
        
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
        
        # Import here to avoid circular imports
        from api_client import fetch_backstage_components_by_system
        
        # Get deprecated entities for efficient lookup
        deprecated_entities = await get_deprecated_entities_set()
        
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
                clean_owner = clean_team_name(comp_owner)
                teams.add(clean_owner)
            
            # Extract APIs from relations
            for relation in relations:
                entity_type, entity_name = parse_backstage_reference(relation.get("targetRef", ""))
                if entity_type == "api":
                    apis.add(entity_name)
        
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
                team = clean_team_name(comp_owner)
            
            if team:
                if team not in teams_in_system:
                    teams_in_system[team] = []
                teams_in_system[team].append(component)
        
        # Add team subgraphs
        for team, team_components in teams_in_system.items():
            mermaid_lines.append(f"        subgraph \"{team}\"")
            for component in team_components:
                comp_name = component["name"]
                comp_var = create_mermaid_variable_name(comp_name)
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
            api_var = create_mermaid_variable_name(api)
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
            comp_var = create_mermaid_variable_name(comp_name)
            relations = component["relations"]
            
            for relation in relations:
                rel_type = relation.get("type", "")
                entity_type, entity_name = parse_backstage_reference(relation.get("targetRef", ""))
                
                if entity_type == "api":
                    api_var = create_mermaid_variable_name(entity_name)
                    if rel_type == "consumesApi":
                        mermaid_lines.append(f"    {comp_var} -->|consumes| {api_var}")
                    elif rel_type == "providesApi":
                        mermaid_lines.append(f"    {comp_var} -->|provides| {api_var}")
                elif entity_type == "component" and rel_type == "dependsOn":
                    dep_var = create_mermaid_variable_name(entity_name)
                    mermaid_lines.append(f"    {comp_var} -.->|depends on| {dep_var}")
        
        mermaid_lines.append("")
        
        # Add styling
        mermaid_lines.extend(get_mermaid_styling_classes())
        
        # Classify and apply styles
        _apply_single_system_styles(mermaid_lines, components, apis, deprecated_entities)
        
        mermaid_lines.append("```")
        
        result = "\n".join(mermaid_lines)
        logger.info(f"Successfully generated single system diagram for: {system_name}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate single system diagram for {system_name}: {e}", exc_info=True)
        return json.dumps({"error": "Diagram generation error", "message": f"Failed to generate single system diagram: {str(e)}", "system": system_name}, indent=2)


def _apply_component_diagram_styles(mermaid_lines: List[str], component_name: str, components: Set[str], 
                                   apis: Set[str], groups: Set[str], systems: Set[str], deprecated_entities: Set[str]):
    """Apply styling to component dependency diagram."""
    main_comp_var = create_mermaid_variable_name(component_name)
    
    # Classify main component
    if component_name in deprecated_entities:
        mermaid_lines.append(f"    class {main_comp_var} deprecated")
    else:
        mermaid_lines.append(f"    class {main_comp_var} service")
    
    # Classify other entities
    component_classification = classify_entities_by_type(components - {component_name}, deprecated_entities, "component")
    api_classification = classify_entities_by_type(apis, deprecated_entities, "api")
    group_classification = classify_entities_by_type(groups, deprecated_entities, "group")
    system_classification = classify_entities_by_type(systems, deprecated_entities, "system")
    
    # Apply styles
    for style_type, entities in component_classification.items():
        if entities and style_type != "deprecated":
            mermaid_lines.append(f"    class {','.join(entities)} {style_type}")
    
    for style_type, entities in api_classification.items():
        if entities and style_type != "deprecated":
            mermaid_lines.append(f"    class {','.join(entities)} {style_type}")
    
    for style_type, entities in group_classification.items():
        if entities and style_type != "deprecated":
            mermaid_lines.append(f"    class {','.join(entities)} {style_type}")
    
    for style_type, entities in system_classification.items():
        if entities and style_type != "deprecated":
            mermaid_lines.append(f"    class {','.join(entities)} {style_type}")
    
    # Apply deprecated styling last
    all_deprecated = (component_classification["deprecated"] + api_classification["deprecated"] + 
                     group_classification["deprecated"] + system_classification["deprecated"])
    if all_deprecated:
        mermaid_lines.append(f"    class {','.join(all_deprecated)} deprecated")


def _apply_systems_overview_styles(mermaid_lines: List[str], all_components: Set[str], all_apis: Set[str], deprecated_entities: Set[str]):
    """Apply styling to systems overview diagram."""
    # Classify components and APIs
    component_classification = classify_entities_by_type(all_components, deprecated_entities, "component")
    api_classification = classify_entities_by_type(all_apis, deprecated_entities, "api")
    
    # Apply component styles
    if component_classification["service"]:
        mermaid_lines.append(f"    class {','.join(component_classification['service'])} service")
    if component_classification["website"]:
        mermaid_lines.append(f"    class {','.join(component_classification['website'])} website")
    
    # Apply API styles
    if api_classification["api"]:
        mermaid_lines.append(f"    class {','.join(api_classification['api'])} api")
    
    # Apply deprecated styling
    all_deprecated = component_classification["deprecated"] + api_classification["deprecated"]
    if all_deprecated:
        mermaid_lines.append(f"    class {','.join(all_deprecated)} deprecated")


def _apply_single_system_styles(mermaid_lines: List[str], components: List[Dict], apis: Set[str], deprecated_entities: Set[str]):
    """Apply styling to single system diagram."""
    # Classify components by type
    service_vars = []
    website_vars = []
    deprecated_component_vars = []
    
    for component in components:
        comp_name = component["name"]
        comp_var = create_mermaid_variable_name(comp_name)
        comp_type = component["type"]
        
        if comp_name in deprecated_entities:
            deprecated_component_vars.append(comp_var)
        elif comp_type == "website":
            website_vars.append(comp_var)
        else:
            service_vars.append(comp_var)
    
    # Apply component styles
    if service_vars:
        mermaid_lines.append(f"    class {','.join(service_vars)} service")
    if website_vars:
        mermaid_lines.append(f"    class {','.join(website_vars)} website")
    
    # Classify APIs
    api_classification = classify_entities_by_type(apis, deprecated_entities, "api")
    if api_classification["api"]:
        mermaid_lines.append(f"    class {','.join(api_classification['api'])} api")
    
    # Apply deprecated styling
    all_deprecated = deprecated_component_vars + api_classification["deprecated"]
    if all_deprecated:
        mermaid_lines.append(f"    class {','.join(all_deprecated)} deprecated")
