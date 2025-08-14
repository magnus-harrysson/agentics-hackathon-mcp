#!/usr/bin/env python3
"""
API client module for handling external API calls.
This module contains all the API-related functionality separated from MCP server logic.
"""

import logging
from typing import Dict, Any
import yaml
import json
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

logger = logging.getLogger("agentics-mcp.api_client")

# OpenAPI specification URL
OPENAPI_SPEC_URL = "https://raw.githubusercontent.com/swagger-api/swagger-petstore/master/src/main/resources/openapi.yaml"


async def get_api_info() -> str:
    """Get basic information about the PET API specification.
    
    Returns:
        Basic information about the PET API including title, version, and description
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(OPENAPI_SPEC_URL)
            response.raise_for_status()
            
        # Parse YAML to extract basic info
        yaml_content = response.text
        parsed_yaml = yaml.safe_load(yaml_content)
        
        info = {
            "title": parsed_yaml.get("info", {}).get("title", "Unknown"),
            "version": parsed_yaml.get("info", {}).get("version", "Unknown"),
            "description": parsed_yaml.get("info", {}).get("description", "No description available"),
            "base_url": parsed_yaml.get("servers", [{}])[0].get("url", "Unknown") if parsed_yaml.get("servers") else "Unknown",
            "paths_count": len(parsed_yaml.get("paths", {})),
            "available_paths": list(parsed_yaml.get("paths", {}).keys())
        }
        
        return json.dumps(info, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting API info: {e}")
        return f"Error: Failed to get API information: {str(e)}"
    

async def fetch_openapi_spec(format: str = "json", save_to_file: str = None) -> str:
    """Fetch the PET API (Swagger Petstore) OpenAPI specification.
    
    Args:
        format: The format to return the specification in ("json" or "yaml")
        save_to_file: Optional file path to save the specification to. If provided, the spec will be saved to this file.
        
    Returns:
        The OpenAPI specification in the requested format, or a success message if saved to file
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(OPENAPI_SPEC_URL)
            response.raise_for_status()
            
        if format.lower() == "yaml":
            content = response.text
        elif format.lower() == "json":
            # Parse YAML and convert to JSON
            yaml_content = response.text
            parsed_yaml = yaml.safe_load(yaml_content)
            content = json.dumps(parsed_yaml, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'yaml'")
        
        # If save_to_file is provided, save the content to the file
        if save_to_file:
            try:
                with open(save_to_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"OpenAPI specification successfully saved to '{save_to_file}' in {format.upper()} format"
            except IOError as e:
                logger.error(f"Error saving file: {e}")
                return f"Error: Failed to save file '{save_to_file}': {str(e)}"
        
        # Otherwise, return the content
        return content
            
    except httpx.HTTPError as e:
        logger.error(f"Error fetching OpenAPI spec: {e}")
        return f"Error: Failed to fetch OpenAPI specification: {str(e)}"
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML: {e}")
        return f"Error: Failed to parse YAML content: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"Error: Unexpected error occurred: {str(e)}"



async def fetch_openapi_spec_raw() -> httpx.Response:
    """Fetch the raw OpenAPI specification response.
    
    Returns:
        The raw HTTP response from the OpenAPI specification URL
        
    Raises:
        httpx.HTTPError: If the request fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(OPENAPI_SPEC_URL)
        response.raise_for_status()
        return response


async def parse_yaml_to_dict(yaml_content: str) -> Dict[str, Any]:
    """Parse YAML content to a dictionary.
    
    Args:
        yaml_content: The YAML content as a string
        
    Returns:
        Parsed YAML as a dictionary
        
    Raises:
        yaml.YAMLError: If YAML parsing fails
    """
    return yaml.safe_load(yaml_content)


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
            "message": "Hello World MCP Server with FastAPI",
            "mcp_server": "hello-world-python",
            "endpoints": {
                "petstore_yaml": "/petstore.yaml",
                "petstore_json": "/petstore.json",
                "docs": "/docs",
                "redoc": "/redoc"
            }
        }

    @api.get("/petstore.yaml")
    async def get_petstore_yaml():
        """Fetch the OpenAPI specification from swagger-petstore repository as YAML."""
        try:
            response = await fetch_openapi_spec_raw()
            return Response(
                content=response.text,
                media_type="application/x-yaml",
                headers={"Content-Disposition": "attachment; filename=openapi.yaml"}
            )
        except Exception as e:
            logger.error(f"Error fetching OpenAPI spec: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch OpenAPI specification: {str(e)}")

    @api.get("/petstore.json")
    async def get_petstore_json():
        """Fetch the OpenAPI specification from swagger-petstore repository as JSON."""
        try:
            response = await fetch_openapi_spec_raw()
            parsed_yaml = await parse_yaml_to_dict(response.text)
            return parsed_yaml
        except Exception as e:
            logger.error(f"Error fetching OpenAPI spec: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch OpenAPI specification: {str(e)}")
