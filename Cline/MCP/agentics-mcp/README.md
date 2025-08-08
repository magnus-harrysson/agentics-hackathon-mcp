# Hello World MCP Server (Python)

A simple "Hello World" Model Context Protocol (MCP) server implemented in Python using fastMCP with FastAPI endpoints. This server demonstrates the basic functionality of MCP by providing greeting and echo tools, plus FastAPI endpoints for fetching OpenAPI specifications.

## Features

### MCP Tools
This MCP server provides three tools:

1. **hello** - Greets a person by name
2. **fetch_pet_api_spec** - Fetch the PET API (Swagger Petstore) OpenAPI specification
3. **get_pet_api_info** - Get basic information about the PET API specification

### FastAPI Endpoints
The server also includes FastAPI endpoints:

1. **GET /** - Root endpoint with server information
2. **GET /petstore.yaml** - Fetch swagger-petstore OpenAPI spec as YAML
3. **GET /petstore.json** - Fetch swagger-petstore OpenAPI spec as JSON
4. **GET /docs** - Interactive API documentation (Swagger UI)
5. **GET /redoc** - Alternative API documentation (ReDoc)

## Requirements

- Python 3.11 or higher
- fastMCP 2.11.2

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

## Usage

The server is designed to be used with MCP-compatible clients. It communicates via stdio (standard input/output).

### Running the server directly

The server supports multiple running modes:

1. **Both MCP and FastAPI servers (default)**:
```bash
python server.py
```

2. **MCP server only**:
```bash
python server.py --mcp-only
```

3. **FastAPI server only**:
```bash
python server.py --fastapi-only
```

When running FastAPI only, the server will be available at `http://localhost:8000`

### Configuration for MCP clients

Add this configuration to your MCP settings file (Replace <path-to-repo>):  

```json
{
  "mcpServers": {
    "hello-world-python": {
      "command": "/<path-to-repo>/agentics-hackathon-mcp/Cline/MCP/agentics-mcp/venv/bin/python",
      "args": ["/<path-to-repo>/agentics-hackathon-mcp/Cline/MCP/agentics-mcp/server.py"]
    }
  }
}
```

## Tools

### hello
Greets a person by name.

**Parameters:**
- `name` (string, required): Name of the person to greet

**Example:**
```json
{
  "name": "Alice"
}
```

**Response:**
```
Hello, Alice! 👋 Welcome to the Hello World MCP server!
```

### fetch_pet_api_spec
Fetch the PET API (Swagger Petstore) OpenAPI specification in JSON or YAML format, with optional file saving capability.

**Parameters:**
- `format` (string, optional): The format to return the specification in ("json" or "yaml"). Default: "json"
- `save_to_file` (string, optional): Optional file path to save the specification to. If provided, the spec will be saved to this file.

**Examples:**

1. Get specification as JSON:
```json
{
  "format": "json"
}
```

2. Get specification as YAML:
```json
{
  "format": "yaml"
}
```

3. Save specification to file:
```json
{
  "format": "json",
  "save_to_file": "petstore-api.json"
}
```

**Response:**
- If `save_to_file` is not provided: Returns the complete OpenAPI specification in the requested format
- If `save_to_file` is provided: Returns a success message confirming the file was saved

### get_pet_api_info
Get basic information about the PET API specification including title, version, description, and available endpoints.

**Parameters:** None

**Example:**
```json
{}
```

**Response:**
```json
{
  "title": "Swagger Petstore - OpenAPI 3.0",
  "version": "1.0.27",
  "description": "This is a sample Pet Store Server based on the OpenAPI 3.0 specification...",
  "base_url": "https://petstore3.swagger.io/api/v3",
  "paths_count": 13,
  "available_paths": ["/pet", "/pet/findByStatus", "/pet/findByTags", ...]
}
```

## Development

This server uses the fastMCP library for simplified MCP server development. The main components are:

- **Server initialization**: Creates a FastMCP server instance
- **Tool registration**: Uses decorators to register tools with automatic schema generation
- **Tool handlers**: Simple functions that implement tool logic
- **Automatic transport**: fastMCP handles stdio communication automatically

## License

This is a simple example project for demonstration purposes.
