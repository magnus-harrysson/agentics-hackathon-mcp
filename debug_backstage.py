#!/usr/bin/env python3
"""
Debug script to test Backstage MCP server tools and see raw responses
"""

import json
import sys
import os
import asyncio
from dotenv import load_dotenv

# Add the MCP server directory to the path
mcp_dir = os.path.join(os.path.dirname(__file__), 'Cline', 'MCP', 'agentics-mcp')
sys.path.append(mcp_dir)

# Load environment variables from .env
env_file = os.path.join(mcp_dir, '.env')
load_dotenv(env_file)

from api_client import (
    fetch_backstage_api_entity, 
    fetch_backstage_component_relations,
    fetch_backstage_systems,
    fetch_backstage_components_by_system,
    fetch_deprecated_entities
)
from config import config

async def main():
    print("=== Backstage MCP Server Debug Tool ===\n")
    
    print("0. Current Configuration:")
    try:
        print(f"BACKSTAGE_BASE_URL: {os.getenv('BACKSTAGE_BASE_URL', 'Not set')}")
        print(f"BACKSTAGE_TOKEN: {'Set' if os.getenv('BACKSTAGE_TOKEN') and os.getenv('BACKSTAGE_TOKEN') != 'your_backstage_token_here' else 'Not set or placeholder'}")
        print(f"Config object: {config.to_dict()}")
        print()
    except Exception as e:
        print(f"Error getting config: {e}")
        print()
    
    print("1. Testing fetch_backstage_systems...")
    try:
        systems_result = await fetch_backstage_systems()
        print("Systems Response:")
        print(systems_result)
        print()
    except Exception as e:
        print(f"Error getting systems: {e}")
        print()
    
    print("2. Testing fetch_backstage_components_by_system for 'commerce'...")
    try:
        components_result = await fetch_backstage_components_by_system("commerce")
        print("Components Response:")
        print(components_result)
        print()
    except Exception as e:
        print(f"Error getting components: {e}")
        print()
    
    print("3. Testing fetch_backstage_component_relations for 'order-service'...")
    try:
        relations_result = await fetch_backstage_component_relations("order-service")
        print("Relations Response:")
        print(relations_result)
        print()
    except Exception as e:
        print(f"Error getting relations: {e}")
        print()
    
    print("4. Testing fetch_backstage_api_entity for 'aldente-service-api'...")
    try:
        api_result = await fetch_backstage_api_entity("aldente-service-api")
        print("API Entity Response:")
        print(api_result)
        print()
    except Exception as e:
        print(f"Error getting API entity: {e}")
        print()

    print("4.5. Testing NEW fetch_deprecated_entities...")
    try:
        deprecated_result = await fetch_deprecated_entities()
        print("Deprecated Entities Response:")
        print(deprecated_result)
        print()
    except Exception as e:
        print(f"Error getting deprecated entities: {e}")
        print()

    print("5. Testing new Mermaid generation tool...")
    try:
        from mcp_client import generate_mermaid_for_component
        
        # Test the mermaid generation directly for order-service (uses deprecated API)
        mermaid_result = await generate_mermaid_for_component("order-service")
        print("Mermaid Diagram for order-service:")
        print(mermaid_result)
        print()
    except Exception as e:
        print(f"Error testing mermaid generation: {e}")
        import traceback
        traceback.print_exc()
        print()

    print("6. Testing new Systems Overview Mermaid tool...")
    try:
        from mcp_client import generate_systems_overview_mermaid_direct
        
        # Test the systems overview mermaid generation
        systems_mermaid_result = await generate_systems_overview_mermaid_direct()
        print("Systems Overview Mermaid Diagram:")
        print(systems_mermaid_result)
        print()
    except Exception as e:
        print(f"Error testing systems overview mermaid generation: {e}")
        import traceback
        traceback.print_exc()
        print()

    print("7. Testing new Single System Mermaid tool...")
    try:
        from mermaid_generator import generate_single_system_diagram
        
        # Test the single system mermaid generation for aldente-app
        single_system_result = await generate_single_system_diagram("aldente-app")
        print("Single System Mermaid Diagram for aldente-app:")
        print(single_system_result)
        print()
    except Exception as e:
        print(f"Error testing single system mermaid generation: {e}")
        import traceback
        traceback.print_exc()
        print()

    print("8. Testing NEW API Migration Plan tool...")
    try:
        from mermaid_generator import generate_api_migration_plan_internal
        
        # Test the migration plan generation for payments API v1 -> v2
        migration_result = await generate_api_migration_plan_internal("payments-api-v1", "payments-api-v2")
        print("API Migration Plan (payments-api-v1 -> payments-api-v2):")
        print(migration_result)
        print()
    except Exception as e:
        print(f"Error testing API migration plan generation: {e}")
        import traceback
        traceback.print_exc()
        print()

if __name__ == "__main__":
    asyncio.run(main())
