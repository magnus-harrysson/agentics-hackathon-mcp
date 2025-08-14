#!/usr/bin/env python3
"""
Utility functions for Mermaid diagram generation.
This module contains shared utility functions used across different diagram generators.
"""

import logging
import json
from typing import Set, Dict, List

logger = logging.getLogger("agentics-mcp.mermaid.utils")


async def get_deprecated_entities_set() -> Set[str]:
    """Get a set of all deprecated entity names for efficient lookup.
    
    Returns:
        Set of deprecated entity names
    """
    try:
        # Import here to avoid circular imports
        from api_client import fetch_deprecated_entities
        
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


async def check_api_lifecycle_batch(api_names: List[str]) -> Dict[str, str]:
    """Check lifecycle status for multiple APIs efficiently.
    
    Args:
        api_names: List of API names to check
        
    Returns:
        Dictionary mapping API names to their lifecycle status
    """
    try:
        # Import here to avoid circular imports
        from api_client import fetch_backstage_api_entity
        
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
    except Exception as e:
        logger.warning(f"Failed to check API lifecycle batch: {e}")
        return {}


def create_mermaid_variable_name(entity_name: str) -> str:
    """Create a valid Mermaid variable name from an entity name.
    
    Args:
        entity_name: The entity name to convert
        
    Returns:
        Valid Mermaid variable name (uppercase, underscores instead of hyphens)
    """
    return entity_name.replace('-', '_').upper()


def get_mermaid_styling_classes() -> List[str]:
    """Get the standard Mermaid CSS styling classes.
    
    Returns:
        List of Mermaid CSS class definitions
    """
    return [
        "    %% Styling with good contrast",
        "    classDef service fill:#2196F3,stroke:#1976D2,stroke-width:2px,color:#ffffff",
        "    classDef api fill:#FF9800,stroke:#F57C00,stroke-width:2px,color:#000000",
        "    classDef group fill:#4CAF50,stroke:#388E3C,stroke-width:2px,color:#ffffff",
        "    classDef system fill:#9C27B0,stroke:#7B1FA2,stroke-width:2px,color:#ffffff",
        "    classDef website fill:#9C27B0,stroke:#7B1FA2,stroke-width:2px,color:#ffffff",
        "    classDef deprecated fill:#FF5722,stroke:#D32F2F,stroke-width:3px,color:#ffffff,stroke-dasharray: 5 5",
        ""
    ]


def classify_entities_by_type(entities: Set[str], deprecated_entities: Set[str], entity_type: str = "component") -> Dict[str, List[str]]:
    """Classify entities by their type and deprecation status.
    
    Args:
        entities: Set of entity names to classify
        deprecated_entities: Set of deprecated entity names
        entity_type: Type of entities being classified (component, api, etc.)
        
    Returns:
        Dictionary with lists of entity variable names by classification
    """
    classification = {
        "deprecated": [],
        "service": [],
        "website": [],
        "api": [],
        "group": [],
        "system": []
    }
    
    for entity in entities:
        entity_var = create_mermaid_variable_name(entity)
        
        if entity in deprecated_entities:
            classification["deprecated"].append(entity_var)
        elif entity_type == "component":
            if 'frontend' in entity.lower() or 'ui' in entity.lower():
                classification["website"].append(entity_var)
            else:
                classification["service"].append(entity_var)
        elif entity_type == "api":
            classification["api"].append(entity_var)
        elif entity_type == "group":
            classification["group"].append(entity_var)
        elif entity_type == "system":
            classification["system"].append(entity_var)
    
    return classification


def parse_backstage_reference(target_ref: str) -> tuple:
    """Parse a Backstage entity reference into type and name.
    
    Args:
        target_ref: Backstage reference (e.g., "api:default/payments-api-v1")
        
    Returns:
        Tuple of (entity_type, entity_name) or (None, None) if invalid
    """
    if not target_ref:
        return None, None
    
    # Handle different reference formats
    if target_ref.startswith("api:default/"):
        return "api", target_ref.replace("api:default/", "")
    elif target_ref.startswith("component:default/"):
        return "component", target_ref.replace("component:default/", "")
    elif target_ref.startswith("group:default/"):
        return "group", target_ref.replace("group:default/", "")
    elif target_ref.startswith("system:default/"):
        return "system", target_ref.replace("system:default/", "")
    else:
        return None, None


def clean_team_name(owner: str) -> str:
    """Clean and normalize team/owner names.
    
    Args:
        owner: Raw owner string from Backstage
        
    Returns:
        Cleaned team name
    """
    if not owner:
        return ""
    
    return owner.replace("group:default/", "").replace("team-", "")
