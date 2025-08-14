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
    fetch_backstage_components_by_system
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

    print("5. Testing new Mermaid generation tool...")
    try:
        from mcp_client import generate_mermaid_for_component
        
        # Test the mermaid generation directly for aldente-frontend
        mermaid_result = await generate_mermaid_for_component("aldente-frontend")
        print("Mermaid Diagram for aldente-frontend:")
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

if __name__ == "__main__":
    asyncio.run(main())
