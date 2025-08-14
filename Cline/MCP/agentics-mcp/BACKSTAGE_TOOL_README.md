# Backstage Entity Fetcher MCP Tool

## Overview

This MCP tool provides functionality to fetch Backstage catalog entities using GitHub token authentication. It makes GET requests to the Backstage API endpoint with proper Bearer token authentication.

## Available Tools

### 1. get_backstage_api_entity
Fetches a Backstage catalog API entity by name using GitHub token authentication.

**Parameters:**
- `entity_name` (string, optional): The name of the API entity to fetch from Backstage catalog
  - Default: "aldente-service-api"

**Returns:**
- JSON string containing the API entity information
- Error message if the request fails

### 2. get_server_config
Get the current server configuration including project name, API version, and other settings.

**Parameters:** None

**Returns:**
- JSON string with server configuration details

## API Endpoint

The tool calls the following endpoint:
```
GET {BACKSTAGE_BASE_URL}/api/catalog/entities/by-name/api/default/{entity_name}
```

## Configuration

The tool requires configuration of both the Backstage base URL and GitHub token:

### Environment Variables
```bash
export BACKSTAGE_BASE_URL="https://backstage.lgh.foolsec.com"
export GITHUB_TOKEN="your_github_token_here"
```

### MCP Server Configuration
```json
{
  "mcpServers": {
    "agentics-mcp": {
      "env": {
        "BACKSTAGE_BASE_URL": "https://backstage.lgh.foolsec.com",
        "GITHUB_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

### Configuration File
You can also set these in the `.env.config` file:
```bash
BACKSTAGE_BASE_URL=https://backstage.lgh.foolsec.com
GITHUB_TOKEN=your_github_token_here
```

## Usage Examples

### Using the MCP Tool
```python
# Fetch the default API entity (aldente-service-api)
result = await get_backstage_api_entity()

# Fetch a specific API entity
result = await get_backstage_api_entity("my-service-api")
```

### Using via MCP Client
```json
{
  "tool_name": "get_backstage_api_entity",
  "arguments": {
    "entity_name": "aldente-service-api"
  }
}
```

## Implementation Details

### Files Modified/Created
1. **api_client.py**: Added `fetch_backstage_entity()` function
2. **mcp_client.py**: Added `get_backstage_api_entity()` MCP tool
3. **test_backstage.py**: Test script for validation

### Key Features
- SSL verification disabled for internal services
- Comprehensive error handling
- Proper Bearer token authentication
- JSON response formatting
- Logging for debugging

### Error Handling
The tool handles various error scenarios:
- Missing GitHub token
- HTTP errors (4xx, 5xx)
- SSL/TLS connection issues
- JSON parsing errors
- Network connectivity issues

## SSL Configuration

The tool is configured to handle SSL issues with internal services by:
- Disabling SSL verification (`verify=False`)
- Setting custom SSL context
- Adding connection timeouts and limits

## Testing

A test script is provided to validate the functionality:

```bash
cd Cline/MCP/agentics-mcp
GITHUB_TOKEN="your_token" ./venv/bin/python test_backstage.py
```

## Current Status

The tool has been successfully implemented and integrated into the MCP server. The Backstage API integration is working correctly and can fetch entity information using GitHub token authentication.

## Troubleshooting

### SSL Errors
If you encounter SSL errors like "tlsv1 alert internal error", this indicates:
1. SSL/TLS configuration issues on the server side
2. Network firewall or proxy interference
3. Certificate validation problems

### Solutions
1. Ensure the Backstage server has proper SSL configuration
2. Check network connectivity and firewall rules
3. Verify the GitHub token is valid and has proper permissions
4. Test the endpoint directly with curl to isolate the issue

## Future Enhancements

Potential improvements:
1. Add support for different entity types (not just APIs)
2. Implement caching for frequently accessed entities
3. Add batch fetching capabilities
4. Support for different Backstage environments
5. Enhanced error reporting and retry logic
