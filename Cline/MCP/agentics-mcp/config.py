#!/usr/bin/env python3
"""
Configuration module for the MCP server.
Handles loading configuration from environment variables only.
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("agentics-mcp.config")


class Config:
    """Configuration class for the MCP server."""
    
    def __init__(self):
        logger.info("Loading configuration from environment variables")
    
    @property
    def backstage_token(self) -> Optional[str]:
        """Get Backstage token from environment variable."""
        return os.getenv('BACKSTAGE_TOKEN')
    
    @property
    def project_name(self) -> str:
        """Get project name from environment variable."""
        return os.getenv('PROJECT_NAME', 'agentics-mcp-project')
    
    @property
    def api_version(self) -> str:
        """Get API version from environment variable."""
        return os.getenv('API_VERSION', 'v1')
    
    @property
    def server_host(self) -> str:
        """Get server host from environment variable or default."""
        return os.getenv('SERVER_HOST', '0.0.0.0')
    
    @property
    def server_port(self) -> int:
        """Get server port from environment variable or default."""
        return int(os.getenv('SERVER_PORT', '8000'))
    
    @property
    def backstage_base_url(self) -> str:
        """Get Backstage base URL from environment variable or default."""
        return os.getenv('BACKSTAGE_BASE_URL', 'https://backstage.lgh.foolsec.com')
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        # Check environment variable (uppercase)
        env_key = key.upper().replace('-', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value
        
        return default
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary (excluding sensitive data)."""
        return {
            'project_name': self.project_name,
            'api_version': self.api_version,
            'server_host': self.server_host,
            'server_port': self.server_port,
            'backstage_token_configured': bool(self.backstage_token),
            'config_source': 'environment_variables'
        }


# Global configuration instance
config = Config()
