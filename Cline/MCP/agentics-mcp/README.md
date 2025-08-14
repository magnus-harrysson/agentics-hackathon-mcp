# MCP Server with OpenAPI functionality

A configurable MCP server with FastAPI endpoints for OpenAPI specification retrieval and GitHub integration.

## Features

- MCP server with tools for fetching OpenAPI specifications
- FastAPI endpoints for direct API access
- Support for both JSON and YAML formats
- Concurrent server operation (MCP + FastAPI)
- Simple environment variable configuration
- GitHub token integration support

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

The server uses environment variables for all configuration. This approach is simple, secure, and follows best practices.

### Setup Configuration

1. Copy the template file:
```bash
cp .env.config .env
```

2. Edit `.env` with your values:
```bash
# MCP Server Configuration
# Copy this file to .env and fill in your values

# Project Configuration
PROJECT_NAME=agentics-mcp-project
API_VERSION=v1

# Fast API Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### Configuration Parameters

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `PROJECT_NAME` | Name of your project | `agentics-mcp-project` |
| `API_VERSION` | Current API version | `v1` |
| `SERVER_HOST` | Server bind address | `0.0.0.0` |
| `SERVER_PORT` | Server port number | `8000` |

**Note**: The GitHub token should be configured in your MCP client configuration (see MCP Client Configuration section below), not in the .env file.

## Usage

### Running the Server

```bash
python server.py
```

The server will start both MCP and FastAPI services concurrently.

### MCP Tools

The server provides these MCP tools:

1. **fetch_api_specs** - Fetch OpenAPI specification in JSON or YAML format
   - Parameters: `format` (json/yaml), `save_to_file` (optional)

2. **get_api_infos** - Get basic information about the API
   - Parameters: None

3. **get_server_config** - Get current server configuration
   - Parameters: None
   - Returns: Current configuration (excluding sensitive data)

### FastAPI Endpoints

- `GET /`: Root endpoint with server information
- `GET /petstore.yaml`: Get OpenAPI spec as YAML
- `GET /petstore.json`: Get OpenAPI spec as JSON
- `GET /docs`: Interactive API documentation
- `GET /redoc`: Alternative API documentation

### MCP Client Configuration

Add this to your MCP client configuration:

```json
{
  "mcpServers": {
    "agentics-mcp": {
      "autoApprove": [],
      "disabled": false,
      "timeout": 10,
      "type": "stdio",
      "command": "/path/to/your/venv/bin/python",
      "args": ["/path/to/your/server.py"],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

**Important**: Replace the paths and values with your actual configuration:
- Update the `command` path to point to your virtual environment's Python executable
- Update the `args` path to point to your server.py file
- Set your actual GitHub token in the `GITHUB_TOKEN` environment variable
- Customize `PROJECT_NAME` and `API_VERSION` as needed

## Development

### Project Structure

```
agentics-mcp/
├── server.py          # Main server entry point
├── mcp_client.py      # MCP server functionality
├── api_client.py      # FastAPI endpoints and API logic
├── config.py          # Configuration management
├── .env.config        # Environment variables template
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

### Adding New Configuration

1. Add the parameter to the `Config` class in `config.py`
2. Add the environment variable to `.env.config`
3. Update this README with the new parameter

### Testing Configuration

Use the `get_server_config` MCP tool to verify your configuration is loaded correctly:

```bash
# This will show current config without sensitive data
python -c "from config import config; print(config.to_dict())"
```

## Requirements

- Python 3.11 or higher
- fastMCP 2.11.2
- FastAPI
- httpx
- PyYAML

## License

This is a demonstration project for MCP server development.
