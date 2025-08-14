#!/usr/bin/env python3
"""
API client module for handling external API calls.
This module contains all the API-related functionality separated from MCP server logic.
"""

import logging
import json
import ssl
import httpx
from fastapi import FastAPI
from config import config

logger = logging.getLogger("agentics-mcp.api_client")


async def fetch_backstage_api_entity(entity_name: str = "aldente-service-api", field: str = "") -> str:
    """Fetch a Backstage catalog API entity by name using GitHub token authentication.
    
    Args:
        entity_name: The name of the API entity to fetch (default: "aldente-service-api")
        field: Specific field to extract from the entity (e.g., "apiVersion", "spec"). If empty, returns full entity.
        
    Returns:
        The API entity information (full or specific field) as JSON string, or error message if failed
    """
    import asyncio
    import random
    
    # Retry configuration
    max_retries = 3
    base_delay = 1.0  # seconds
    
    for attempt in range(max_retries):
        try:
            # Check if Backstage token is configured
            backstage_token = config.backstage_token
            if not backstage_token:
                return "Error: Backstage token not configured. Please set the BACKSTAGE_TOKEN environment variable."
            
            # Construct the URL using configured base URL
            base_url = f"{config.backstage_base_url}/api/catalog/entities/by-name/api/default"
            url = f"{base_url}/{entity_name}"
            
            # Set up headers with Bearer token
            headers = {
                "Authorization": f"Bearer {backstage_token}",
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
                logger.info(f"Making request to: {url} (attempt {attempt + 1}/{max_retries})")
                logger.info(f"Headers: {headers}")
                response = await client.get(url, headers=headers)
                logger.info(f"Response status: {response.status_code}")
                response.raise_for_status()
                
            # Get the response data and clean up newline characters
            response_data = response.json()
            
            # If a specific field is requested, extract it
            if field:
                field_data = response_data.get(field, [])
                logger.info(f"Successfully fetched API entity {entity_name} on attempt {attempt + 1}")
                return json.dumps(field_data, indent=2)
            
            # Return the response as formatted JSON
            logger.info(f"Successfully fetched API entity {entity_name} on attempt {attempt + 1}")
            return json.dumps(response_data, indent=2)
            
        except (httpx.HTTPError, ssl.SSLError) as e:
            # Network or SSL error - retry with exponential backoff
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(f"Network/SSL error on attempt {attempt + 1}/{max_retries}: {e}. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                continue
            else:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                return f"Error: Failed to fetch Backstage entity after {max_retries} attempts: {str(e)}"
                
        except httpx.HTTPStatusError as e:
            # HTTP error - don't retry for client errors (4xx)
            if e.response.status_code < 500:
                logger.error(f"HTTP client error {e.response.status_code}: {e}")
                return f"Error: HTTP {e.response.status_code} - {e.response.text}"
            # Server error (5xx) - retry
            elif attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(f"HTTP server error {e.response.status_code} on attempt {attempt + 1}/{max_retries}. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                continue
            else:
                logger.error(f"HTTP error after {max_retries} attempts: {e}")
                return f"Error: HTTP {e.response.status_code} after {max_retries} attempts - {e.response.text}"
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return f"Error: Failed to parse JSON response: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error fetching Backstage entity: {e}")
            return f"Error: Unexpected error occurred: {str(e)}"
    
    # Should not reach here, but just in case
    return f"Error: Failed to fetch Backstage entity after {max_retries} attempts"


async def fetch_backstage_component_relations(component_name: str = "aldente-service") -> str:
    """Fetch a Backstage catalog component entity and return only its relations.
    
    Args:
        component_name: The name of the component to fetch (default: "aldente-service")
        
    Returns:
        The component relations as JSON string, or error message if failed
    """
    import asyncio
    import random
    
    # Retry configuration
    max_retries = 3
    base_delay = 1.0  # seconds
    
    for attempt in range(max_retries):
        try:
            # Check if Backstage token is configured
            backstage_token = config.backstage_token
            if not backstage_token:
                return "Error: Backstage token not configured. Please set the BACKSTAGE_TOKEN environment variable."
            
            # Construct the URL using configured base URL for component entities
            base_url = f"{config.backstage_base_url}/api/catalog/entities/by-name/component/default"
            url = f"{base_url}/{component_name}"
            
            # Set up headers with Bearer token
            headers = {
                "Authorization": f"Bearer {backstage_token}",
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
                logger.info(f"Making request to: {url} (attempt {attempt + 1}/{max_retries})")
                response = await client.get(url, headers=headers)
                logger.info(f"Response status: {response.status_code}")
                response.raise_for_status()
                
            # Parse the response and extract only the relations
            entity_data = response.json()
            relations = entity_data.get("relations", [])
            
            # Success - return the relations
            logger.info(f"Successfully fetched relations for {component_name} on attempt {attempt + 1}")
            return json.dumps(relations, indent=2)
            
        except (httpx.HTTPError, ssl.SSLError) as e:
            # Network or SSL error - retry with exponential backoff
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(f"Network/SSL error on attempt {attempt + 1}/{max_retries}: {e}. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                continue
            else:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                return f"Error: Failed to fetch Backstage component after {max_retries} attempts: {str(e)}"
                
        except httpx.HTTPStatusError as e:
            # HTTP error - don't retry for client errors (4xx)
            if e.response.status_code < 500:
                logger.error(f"HTTP client error {e.response.status_code}: {e}")
                return f"Error: HTTP {e.response.status_code} - {e.response.text}"
            # Server error (5xx) - retry
            elif attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(f"HTTP server error {e.response.status_code} on attempt {attempt + 1}/{max_retries}. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                continue
            else:
                logger.error(f"HTTP error after {max_retries} attempts: {e}")
                return f"Error: HTTP {e.response.status_code} after {max_retries} attempts - {e.response.text}"
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return f"Error: Failed to parse JSON response: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error fetching Backstage component: {e}")
            return f"Error: Unexpected error occurred: {str(e)}"
    
    # Should not reach here, but just in case
    return f"Error: Failed to fetch Backstage component after {max_retries} attempts"


async def fetch_backstage_systems(base_url: str = None) -> str:
    """Fetch all systems from Backstage catalog by querying components and extracting their systems.
    
    Args:
        base_url: Optional base URL override for Backstage API
        
    Returns:
        List of unique systems as JSON string, or error message if failed
    """
    import asyncio
    import random
    
    # Retry configuration
    max_retries = 3
    base_delay = 1.0  # seconds
    
    for attempt in range(max_retries):
        try:
            # Check if Backstage token is configured
            backstage_token = config.backstage_token
            if not backstage_token:
                return json.dumps({"error": "Backstage token not configured", "message": "Please set the BACKSTAGE_TOKEN environment variable."}, indent=2)
            
            # Use provided base URL or fall back to config
            api_base_url = base_url or config.backstage_base_url
            url = f"{api_base_url}/api/catalog/entities/by-query?filter=kind=component&fields=spec.system"
            
            # Set up headers with Bearer token
            headers = {
                "Authorization": f"Bearer {backstage_token}",
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
                logger.info(f"Making request to: {url} (attempt {attempt + 1}/{max_retries})")
                response = await client.get(url, headers=headers)
                logger.info(f"Response status: {response.status_code}")
                response.raise_for_status()
                
            # Get the response data
            response_data = response.json()
            
            # Extract unique systems from the components
            systems = set()
            for item in response_data.get('items', []):
                spec = item.get('spec', {})
                system = spec.get('system')
                if system:
                    systems.add(system)
            
            # Convert to sorted list and return as JSON
            systems_list = sorted(list(systems))
            result = {
                "systems": systems_list,
                "total_systems": len(systems_list),
                "total_components": len(response_data.get('items', []))
            }
            
            logger.info(f"Successfully fetched systems on attempt {attempt + 1}")
            return json.dumps(result, indent=2)
            
        except (httpx.HTTPError, ssl.SSLError) as e:
            # Network or SSL error - retry with exponential backoff
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(f"Network/SSL error on attempt {attempt + 1}/{max_retries}: {e}. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                continue
            else:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                return json.dumps({"error": "Network error", "message": f"Failed to fetch Backstage systems after {max_retries} attempts: {str(e)}"}, indent=2)
                
        except httpx.HTTPStatusError as e:
            # HTTP error - don't retry for client errors (4xx)
            if e.response.status_code < 500:
                logger.error(f"HTTP client error {e.response.status_code}: {e}")
                return json.dumps({"error": f"HTTP {e.response.status_code}", "message": str(e.response.text)}, indent=2)
            # Server error (5xx) - retry
            elif attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(f"HTTP server error {e.response.status_code} on attempt {attempt + 1}/{max_retries}. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                continue
            else:
                logger.error(f"HTTP error after {max_retries} attempts: {e}")
                return json.dumps({"error": f"HTTP {e.response.status_code}", "message": f"Server error after {max_retries} attempts: {e.response.text}"}, indent=2)
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return json.dumps({"error": "JSON parsing error", "message": f"Failed to parse JSON response: {str(e)}"}, indent=2)
        except Exception as e:
            logger.error(f"Unexpected error fetching Backstage systems: {e}", exc_info=True)
            return json.dumps({"error": "Unexpected error", "message": str(e)}, indent=2)
    
    # Should not reach here, but just in case
    return json.dumps({"error": "Failed", "message": f"Failed to fetch Backstage systems after {max_retries} attempts"}, indent=2)


async def fetch_backstage_components_by_system(system_name: str, base_url: str = None) -> str:
    """Fetch all components for a specific system from Backstage catalog.
    
    Args:
        system_name: The name of the system to filter components by
        base_url: Optional base URL override for Backstage API
        
    Returns:
        List of components in the system as JSON string, or error message if failed
    """
    import asyncio
    import random
    
    # Retry configuration
    max_retries = 3
    base_delay = 1.0  # seconds
    
    for attempt in range(max_retries):
        try:
            # Check if Backstage token is configured
            backstage_token = config.backstage_token
            if not backstage_token:
                return json.dumps({"error": "Backstage token not configured", "message": "Please set the BACKSTAGE_TOKEN environment variable."}, indent=2)
            
            # Use provided base URL or fall back to config
            api_base_url = base_url or config.backstage_base_url
            url = f"{api_base_url}/api/catalog/entities/by-query?filter=kind=component,spec.system={system_name}"
            
            # Set up headers with Bearer token
            headers = {
                "Authorization": f"Bearer {backstage_token}",
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
                logger.info(f"Making request to: {url} (attempt {attempt + 1}/{max_retries})")
                response = await client.get(url, headers=headers)
                logger.info(f"Response status: {response.status_code}")
                response.raise_for_status()
                
            # Get the response data
            response_data = response.json()
            
            # Extract component information
            components = []
            for item in response_data.get('items', []):
                component_info = {
                    "name": item.get('metadata', {}).get('name', 'Unknown'),
                    "namespace": item.get('metadata', {}).get('namespace', 'default'),
                    "title": item.get('metadata', {}).get('title', ''),
                    "description": item.get('metadata', {}).get('description', ''),
                    "system": item.get('spec', {}).get('system', ''),
                    "type": item.get('spec', {}).get('type', ''),
                    "lifecycle": item.get('spec', {}).get('lifecycle', ''),
                    "owner": item.get('spec', {}).get('owner', '')
                }
                components.append(component_info)
            
            result = {
                "system": system_name,
                "components": components,
                "total_components": len(components)
            }
            
            logger.info(f"Successfully fetched components for system {system_name} on attempt {attempt + 1}")
            return json.dumps(result, indent=2)
            
        except (httpx.HTTPError, ssl.SSLError) as e:
            # Network or SSL error - retry with exponential backoff
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(f"Network/SSL error on attempt {attempt + 1}/{max_retries}: {e}. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                continue
            else:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                return json.dumps({"error": "Network error", "message": f"Failed to fetch Backstage components after {max_retries} attempts: {str(e)}", "system": system_name}, indent=2)
                
        except httpx.HTTPStatusError as e:
            # HTTP error - don't retry for client errors (4xx)
            if e.response.status_code < 500:
                logger.error(f"HTTP client error {e.response.status_code}: {e}")
                return json.dumps({"error": f"HTTP {e.response.status_code}", "message": str(e.response.text), "system": system_name}, indent=2)
            # Server error (5xx) - retry
            elif attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(f"HTTP server error {e.response.status_code} on attempt {attempt + 1}/{max_retries}. Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                continue
            else:
                logger.error(f"HTTP error after {max_retries} attempts: {e}")
                return json.dumps({"error": f"HTTP {e.response.status_code}", "message": f"Server error after {max_retries} attempts: {e.response.text}", "system": system_name}, indent=2)
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return json.dumps({"error": "JSON parsing error", "message": f"Failed to parse JSON response: {str(e)}", "system": system_name}, indent=2)
        except Exception as e:
            logger.error(f"Unexpected error fetching Backstage components by system: {e}", exc_info=True)
            return json.dumps({"error": "Unexpected error", "message": str(e), "system": system_name}, indent=2)
    
    # Should not reach here, but just in case
    return json.dumps({"error": "Failed", "message": f"Failed to fetch Backstage components after {max_retries} attempts", "system": system_name}, indent=2)


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
