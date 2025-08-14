#!/usr/bin/env python3
"""
API client module for handling external API calls.
This module contains all the API-related functionality separated from MCP server logic.
"""

import logging
import json
import httpx
from fastapi import FastAPI
from config import config

logger = logging.getLogger("agentics-mcp.api_client")


async def fetch_backstage_api_entity(entity_name: str = "aldente-service-api") -> str:
    """Fetch a Backstage catalog API entity by name using GitHub token authentication.
    
    Args:
        entity_name: The name of the API entity to fetch (default: "aldente-service-api")
        
    Returns:
        The API entity information as JSON string, or error message if failed
    """
    try:
        # Check if GitHub token is configured
        github_token = config.github_token
        if not github_token:
            return "Error: GitHub token not configured. Please set the GITHUB_TOKEN environment variable."
        
        # Construct the URL using configured base URL
        base_url = f"{config.backstage_base_url}/api/catalog/entities/by-name/api/default"
        url = f"{base_url}/{entity_name}"
        
        # Set up headers with Bearer token
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Make the API call with enhanced SSL configuration
        import ssl
        
        # Create a more permissive SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        ssl_context.set_ciphers('DEFAULT:@SECLEVEL=1')
        
        async with httpx.AsyncClient(
            verify=ssl_context, 
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            http2=False  # Disable HTTP/2 to avoid potential issues
        ) as client:
            logger.info(f"Making request to: {url}")
            logger.info(f"Headers: {headers}")
            response = await client.get(url, headers=headers)
            logger.info(f"Response status: {response.status_code}")
            response.raise_for_status()
            
        # Get the response data s
        response_data = response.json()
        
        # Return the response as formatted JSON
        return json.dumps(response_data, indent=2)
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching Backstage entity: {e}")
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.HTTPError as e:
        logger.error(f"Error fetching Backstage entity: {e}")
        return f"Error: Failed to fetch Backstage entity: {str(e)}"
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {e}")
        return f"Error: Failed to parse JSON response: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error fetching Backstage entity: {e}")
        return f"Error: Unexpected error occurred: {str(e)}"


async def fetch_backstage_component_relations(component_name: str = "aldente-service") -> str:
    """Fetch a Backstage catalog component entity and return only its relations.
    
    Args:
        component_name: The name of the component to fetch (default: "aldente-service")
        
    Returns:
        The component relations as JSON string, or error message if failed
    """
    try:
        # Check if GitHub token is configured
        github_token = config.github_token
        if not github_token:
            return "Error: GitHub token not configured. Please set the GITHUB_TOKEN environment variable."
        
        # Construct the URL using configured base URL for component entities
        base_url = f"{config.backstage_base_url}/api/catalog/entities/by-name/component/default"
        url = f"{base_url}/{component_name}"
        
        # Set up headers with Bearer token
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Make the API call with SSL verification disabled for internal services
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        async with httpx.AsyncClient(
            verify=False, 
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        ) as client:
            logger.info(f"Making request to: {url}")
            logger.info(f"Headers: {headers}")
            response = await client.get(url, headers=headers)
            logger.info(f"Response status: {response.status_code}")
            response.raise_for_status()
            
        # Parse the response and extract only the relations
        entity_data = response.json()
        relations = entity_data.get("relations", [])
        
        # Return only the relations as formatted JSON
        return json.dumps(relations, indent=2)
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching Backstage component: {e}")
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.HTTPError as e:
        logger.error(f"Error fetching Backstage component: {e}")
        return f"Error: Failed to fetch Backstage component: {str(e)}"
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {e}")
        return f"Error: Failed to parse JSON response: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error fetching Backstage component: {e}")
        return f"Error: Unexpected error occurred: {str(e)}"


# FastAPI endpoints
def create_api_routes(api: FastAPI):
    """Create and register API routes with the FastAPI app.
    
    Args:
        api: The FastAPI application instance
    """
    
    @api.get("/")
    async def root():
        """Root endpoint with basic information."""
        return {
            "message": "Backstage MCP Server with FastAPI",
            "mcp_server": "agentics-mcp",
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc"
            }
        }
