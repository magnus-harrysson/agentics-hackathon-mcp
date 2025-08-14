#!/usr/bin/env python3
"""
Mermaid diagram generation package for Backstage components and systems.

This package provides modular functionality for:
- Generating component dependency diagrams
- Creating systems overview diagrams
- Producing single system architecture diagrams
- Analyzing API migrations
- Generating comprehensive migration guides

The package maintains backward compatibility with the original mermaid_generator.py interface.
"""

# Import all public functions to maintain backward compatibility
from .diagram_generators import (
    generate_component_dependency_diagram,
    generate_systems_overview_diagram,
    generate_single_system_diagram
)

from .migration_guide import (
    generate_api_migration_plan_internal
)

from .utils import (
    get_deprecated_entities_set,
    check_api_lifecycle_batch
)

from .migration_analyzer import (
    parse_openapi_definition,
    analyze_api_migration_fast,
    generate_migration_steps_fast,
    generate_typescript_migration_examples
)

# Export all public functions
__all__ = [
    # Diagram generation functions
    'generate_component_dependency_diagram',
    'generate_systems_overview_diagram', 
    'generate_single_system_diagram',
    
    # Migration functions
    'generate_api_migration_plan_internal',
    
    # Utility functions
    'get_deprecated_entities_set',
    'check_api_lifecycle_batch',
    
    # Migration analysis functions
    'parse_openapi_definition',
    'analyze_api_migration_fast',
    'generate_migration_steps_fast',
    'generate_typescript_migration_examples'
]

# Package metadata
__version__ = "1.0.0"
__author__ = "Agentics MCP Team"
__description__ = "Modular Mermaid diagram generation for Backstage"
