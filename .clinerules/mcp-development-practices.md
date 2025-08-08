## Brief overview
Guidelines for developing and maintaining MCP (Model Context Protocol) servers, with emphasis on proper documentation, testing, and incremental feature enhancement. These rules are based on working with Python MCP servers using fastMCP library.

## Communication style
- Provide clear, technical explanations without conversational fluff
- Avoid starting responses with "Great", "Certainly", "Okay", or "Sure"
- Be direct and to the point when explaining technical concepts
- Include practical examples and code snippets when demonstrating functionality

## Development workflow
- Make incremental changes to existing functionality rather than complete rewrites
- Test new features with standalone test scripts before integrating into main codebase
- Wait for confirmation of successful tool execution before proceeding to next steps
- Use replace_in_file for targeted changes to preserve existing functionality

## MCP server best practices
- Maintain backward compatibility when adding new optional parameters to existing tools
- Include comprehensive error handling for file operations and network requests
- Use descriptive parameter names and provide clear docstrings for all tools
- Support both return-content and save-to-file patterns for data retrieval tools

## Documentation maintenance
- Keep README.md files synchronized with new capabilities immediately after implementation
- Document all tool parameters with types, requirements, and examples
- Include both simple and advanced usage examples for complex tools
- Provide clear response format documentation with sample JSON outputs

## Testing approach
- Create standalone test scripts to validate new functionality before MCP integration
- Test both success and error scenarios for file operations
- Verify that optional parameters work correctly with default values
- Demonstrate functionality with concrete examples that produce visible results

## Code organization
- Use async/await patterns consistently for network operations
- Implement proper exception handling with informative error messages
- Structure tools with clear separation between parameter validation, business logic, and response formatting
- Maintain consistent naming conventions using snake_case for parameters
