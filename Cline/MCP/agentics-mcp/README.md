# Backstage MCP Server

A robust MCP server providing tools for interacting with Backstage catalog entities with built-in retry logic for reliability.

## Features

- **Backstage Integration**: Fetch API entities, component relations, systems, and components
- **Robust Retry Logic**: Exponential backoff with jitter for handling transient network/SSL errors
- **Backstage Token Authentication**: Secure authentication using Backstage tokens
- **Comprehensive Error Handling**: Smart error categorization and recovery
- **FastAPI Endpoints**: Direct API access for testing and debugging
- **Environment Variable Configuration**: Simple and secure configuration management

## Available MCP Tools

### 1. `get_backstage_api_entity`
Fetch a Backstage catalog API entity by name.

**Parameters:**
- `entity_name` (optional): Name of the API entity (default: "aldente-service-api")
- `field` (optional): Specific field to extract from the entity

**Returns:** Complete API entity information as JSON

### 2. `get_backstage_component_relations`
Fetch component relations from Backstage catalog.

**Parameters:**
- `component_name` (optional): Name of the component (default: "aldente-service")

**Returns:** Array of component relations

### 3. `list_backstage_systems`
List all unique systems from the Backstage catalog.

**Parameters:**
- `base_url` (optional): Override the default Backstage API base URL

**Returns:** List of systems with counts

### 4. `list_backstage_components_by_system`
List all components belonging to a specific system.

**Parameters:**
- `system_name` (required): Name of the system to filter by
- `base_url` (optional): Override the default Backstage API base URL

**Returns:** Detailed component information for the system

### 5. `get_server_config`
Get current server configuration.

**Parameters:** None

**Returns:** Server configuration details (excluding sensitive data)

## Installation

1. Create a virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Required Environment Variables

The server requires these environment variables to be configured:

| Variable | Description | Required |
|----------|-------------|----------|
| `BACKSTAGE_BASE_URL` | Base URL for your Backstage instance | Yes |
| `BACKSTAGE_TOKEN` | Backstage authentication token | Yes |
| `PROJECT_NAME` | Project name | No (default: agentics-mcp-project) |
| `API_VERSION` | API version | No (default: v1) |
| `SERVER_HOST` | Server host | No (default: 0.0.0.0) |
| `SERVER_PORT` | Server port | No (default: 8000) |


### Setup Configuration

1. Copy the template file:
```bash
cp .env.config .env
```

2. Edit `.env` with your values:
```bash
# Backstage Configuration
BACKSTAGE_BASE_URL=https://your-backstage-instance.com
BACKSTAGE_TOKEN=your_backstage_token_here

# Server Configuration
PROJECT_NAME=agentics-mcp-project
API_VERSION=v1
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

## Usage

### Running the Server

```bash
python mcp_server_only.py
```

### MCP Client Configuration

Add this to your MCP client configuration:

```json
{
  "mcpServers": {
    "agentics-mcp": {
      "command": "/path/to/your/venv/bin/python",
      "args": ["/path/to/your/mcp_server_only.py"],
      "env": {
        "BACKSTAGE_BASE_URL": "https://your-backstage-instance.com",
        "BACKSTAGE_TOKEN": "your_backstage_token_here"
      }
    }
  }
}
```

### Example Usage

```python
# List all systems
await use_mcp_tool("agentics-mcp", "list_backstage_systems", {})

# Get components for a specific system
await use_mcp_tool("agentics-mcp", "list_backstage_components_by_system", {
    "system_name": "commerce"
})

# Get API entity details
await use_mcp_tool("agentics-mcp", "get_backstage_api_entity", {
    "entity_name": "aldente-service-api"
})

# Get component relations
await use_mcp_tool("agentics-mcp", "get_backstage_component_relations", {
    "component_name": "aldente-service"
})
```

## Retry Logic

All API functions include robust retry logic:

- **Max Retries**: 3 attempts
- **Backoff Strategy**: Exponential (2^attempt) with random jitter (0-0.5 seconds)
- **Smart Error Handling**: 
  - Retries on network/SSL errors and 5xx server errors
  - No retry on 4xx client errors
  - Immediate failure on JSON parsing errors

## Error Handling

The server provides comprehensive error handling:

- **Network/SSL Errors**: Automatic retry with exponential backoff
- **HTTP Errors**: Smart categorization (retry 5xx, fail 4xx)
- **Authentication Errors**: Clear error messages for missing tokens
- **JSON Parsing Errors**: Detailed error information

## Project Structure

```
agentics-mcp/
├── mcp_server_only.py    # Main MCP server entry point
├── api_client.py         # API functions with retry logic
├── config.py            # Configuration management
├── .env.config          # Environment variables template
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Requirements

- Python 3.11 or higher
- mcp 1.1.0
- httpx
- fastapi
- PyYAML

## Troubleshooting

### SSL Errors
If you encounter SSL errors:
1. Check network connectivity to your Backstage instance
2. Verify SSL certificates are properly configured
3. The retry logic will automatically handle transient SSL issues

### Authentication Errors
If you get authentication errors:
1. Verify your Backstage token is valid
2. Ensure the token has proper permissions for your Backstage instance
3. Check that the token is correctly set in your environment (use `BACKSTAGE_TOKEN`)

### Configuration Issues
Use the `get_server_config` tool to verify your configuration is loaded correctly.

## License

This is a demonstration project for MCP server development with Backstage integration.
