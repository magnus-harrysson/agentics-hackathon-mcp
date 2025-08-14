#!/usr/bin/env python3
"""
API migration analysis module.
This module contains functions for analyzing API migrations and generating migration steps.
"""

import logging
import json
from typing import Dict, List, Set

logger = logging.getLogger("agentics-mcp.mermaid.migration_analyzer")


def parse_openapi_definition(definition: str) -> Dict:
    """Parse OpenAPI definition from YAML or JSON string.
    
    Args:
        definition: OpenAPI definition as YAML or JSON string
        
    Returns:
        Parsed OpenAPI specification as dictionary, or empty dict if parsing fails
    """
    try:
        import yaml
        # Try YAML first (most common for OpenAPI)
        return yaml.safe_load(definition)
    except:
        try:
            # Fallback to JSON
            return json.loads(definition)
        except:
            logger.warning("Failed to parse OpenAPI definition as YAML or JSON")
            return {}


def analyze_api_migration_fast(from_openapi: Dict, to_openapi: Dict, from_api: str, to_api: str) -> Dict:
    """Fast API migration analysis without additional API calls.
    
    Args:
        from_openapi: Source API OpenAPI specification
        to_openapi: Target API OpenAPI specification
        from_api: Source API name
        to_api: Target API name
        
    Returns:
        Comprehensive migration analysis with breaking changes, examples, and recommendations
    """
    analysis = {
        "complexity": "medium",
        "estimated_effort": "2-4 hours",
        "breaking_changes": [],
        "new_features": [],
        "removed_features": [],
        "migration_steps": [],
        "typescript_examples": {},
        "testing_recommendations": [],
        "rollback_strategy": {}
    }
    
    from_paths = from_openapi.get("paths", {})
    to_paths = to_openapi.get("paths", {})
    
    # Analyze endpoint changes
    from_endpoints = set(from_paths.keys())
    to_endpoints = set(to_paths.keys())
    
    removed_endpoints = from_endpoints - to_endpoints
    new_endpoints = to_endpoints - from_endpoints
    common_endpoints = from_endpoints & to_endpoints
    
    # Track breaking changes
    if removed_endpoints:
        for endpoint in removed_endpoints:
            analysis["breaking_changes"].append({
                "type": "endpoint_removed",
                "endpoint": endpoint,
                "impact": "high",
                "description": f"Endpoint {endpoint} has been removed and is no longer available"
            })
            analysis["removed_features"].append(f"Endpoint: {endpoint}")
    
    if new_endpoints:
        for endpoint in new_endpoints:
            analysis["new_features"].append(f"New endpoint: {endpoint}")
    
    # Analyze common endpoints for changes
    for endpoint in common_endpoints:
        from_endpoint = from_paths[endpoint]
        to_endpoint = to_paths[endpoint]
        
        # Check for method changes
        from_methods = set(from_endpoint.keys())
        to_methods = set(to_endpoint.keys())
        
        removed_methods = from_methods - to_methods
        new_methods = to_methods - from_methods
        
        if removed_methods:
            for method in removed_methods:
                analysis["breaking_changes"].append({
                    "type": "method_removed",
                    "endpoint": endpoint,
                    "method": method.upper(),
                    "impact": "high",
                    "description": f"HTTP method {method.upper()} removed from {endpoint}"
                })
        
        # Analyze request/response schema changes for common methods
        common_methods = from_methods & to_methods
        for method in common_methods:
            if method in ["get", "post", "put", "patch", "delete"]:
                method_changes = analyze_method_changes(
                    from_endpoint.get(method, {}), 
                    to_endpoint.get(method, {}), 
                    endpoint, 
                    method
                )
                analysis["breaking_changes"].extend(method_changes["breaking_changes"])
                analysis["new_features"].extend(method_changes["new_features"])
    
    # Generate migration complexity assessment
    breaking_change_count = len(analysis["breaking_changes"])
    if breaking_change_count == 0:
        analysis["complexity"] = "low"
        analysis["estimated_effort"] = "1-2 hours"
    elif breaking_change_count <= 3:
        analysis["complexity"] = "medium"
        analysis["estimated_effort"] = "2-4 hours"
    else:
        analysis["complexity"] = "high"
        analysis["estimated_effort"] = "4-8 hours"
    
    # Generate migration steps
    analysis["migration_steps"] = generate_migration_steps_fast(analysis)
    
    return analysis


def analyze_method_changes(from_method: Dict, to_method: Dict, endpoint: str, method: str) -> Dict:
    """Analyze changes in a specific HTTP method between API versions."""
    changes = {
        "breaking_changes": [],
        "new_features": []
    }
    
    # Check request body changes
    from_request_body = from_method.get("requestBody", {})
    to_request_body = to_method.get("requestBody", {})
    
    # Check if request body became required
    if not from_request_body.get("required", False) and to_request_body.get("required", False):
        changes["breaking_changes"].append({
            "type": "request_body_required",
            "endpoint": endpoint,
            "method": method.upper(),
            "impact": "medium",
            "description": f"Request body is now required for {method.upper()} {endpoint}"
        })
    
    # Check parameter changes
    from_params = from_method.get("parameters", [])
    to_params = to_method.get("parameters", [])
    
    from_param_names = {p.get("name") for p in from_params if p.get("name")}
    to_param_names = {p.get("name") for p in to_params if p.get("name")}
    
    removed_params = from_param_names - to_param_names
    new_params = to_param_names - from_param_names
    
    for param in removed_params:
        changes["breaking_changes"].append({
            "type": "parameter_removed",
            "endpoint": endpoint,
            "method": method.upper(),
            "parameter": param,
            "impact": "medium",
            "description": f"Parameter '{param}' removed from {method.upper()} {endpoint}"
        })
    
    for param in new_params:
        # Check if new parameter is required
        param_info = next((p for p in to_params if p.get("name") == param), {})
        if param_info.get("required", False):
            changes["breaking_changes"].append({
                "type": "required_parameter_added",
                "endpoint": endpoint,
                "method": method.upper(),
                "parameter": param,
                "impact": "high",
                "description": f"New required parameter '{param}' added to {method.upper()} {endpoint}"
            })
        else:
            changes["new_features"].append(f"New optional parameter '{param}' in {method.upper()} {endpoint}")
    
    return changes


def generate_migration_steps_fast(analysis: Dict) -> List[Dict]:
    """Generate step-by-step migration instructions (fast version)."""
    steps = [
        {
            "step": 1,
            "title": "Review Breaking Changes",
            "description": "Carefully review all breaking changes identified in this migration plan",
            "action": "Analyze the impact of each breaking change on your application"
        },
        {
            "step": 2,
            "title": "Update API Client Configuration",
            "description": "Update your API client to point to the new API version",
            "action": "Change base URL, API version, and any authentication requirements"
        },
        {
            "step": 3,
            "title": "Update Request/Response Handling",
            "description": "Modify your code to handle changes in request and response formats",
            "action": "Update data structures, field names, and validation logic"
        },
        {
            "step": 4,
            "title": "Implement Error Handling",
            "description": "Update error handling for new error codes and response formats",
            "action": "Test error scenarios and update exception handling"
        },
        {
            "step": 5,
            "title": "Test Migration",
            "description": "Thoroughly test the migration with comprehensive test cases",
            "action": "Run unit tests, integration tests, and manual testing"
        },
        {
            "step": 6,
            "title": "Deploy and Monitor",
            "description": "Deploy the changes and monitor for any issues",
            "action": "Deploy to staging first, then production with careful monitoring"
        }
    ]
    
    # Add specific steps based on breaking changes
    if any(change["type"] == "endpoint_removed" for change in analysis["breaking_changes"]):
        steps.insert(2, {
            "step": "2a",
            "title": "Handle Removed Endpoints",
            "description": "Update code that calls removed endpoints",
            "action": "Find alternative endpoints or remove functionality that depends on removed endpoints"
        })
    
    return steps


def generate_typescript_migration_examples(from_openapi: Dict, to_openapi: Dict, from_api: str, to_api: str) -> Dict:
    """Generate TypeScript code examples for the migration."""
    examples = {}
    
    from_paths = from_openapi.get("paths", {})
    to_paths = to_openapi.get("paths", {})
    
    # Generate basic client setup example
    examples["client_setup"] = {
        "description": "Update your API client configuration",
        "before": f'''// Old API client setup
interface PaymentRequestV1 {{
  amountCents: number;
  currency: string;
}}

interface PaymentResponseV1 {{
  id: string;
  status: string;
  amountCents: number;
  currency: string;
}}

class {from_api.replace("-", "_").title()}Client {{
  private baseUrl = "http://localhost:4010";

  async createPayment(request: PaymentRequestV1): Promise<PaymentResponseV1> {{
    const response = await fetch(`${{this.baseUrl}}/payments`, {{
      method: 'POST',
      headers: {{
        'Content-Type': 'application/json',
      }},
      body: JSON.stringify(request),
    }});
    return response.json();
  }}
}}''',
        "after": f'''// New API client setup
import {{ v4 as uuidv4 }} from 'uuid';

interface PaymentRequestV2 {{
  amount: number;
  currency: string;
}}

interface PaymentResponseV2 {{
  paymentId: string;
  state: string;
  amount: number;
  currency: string;
}}

class {to_api.replace("-", "_").title()}Client {{
  private baseUrl = "http://localhost:4011";

  async createPayment(request: PaymentRequestV2): Promise<PaymentResponseV2> {{
    const response = await fetch(`${{this.baseUrl}}/v2/payments`, {{
      method: 'POST',
      headers: {{
        'Content-Type': 'application/json',
        'Idempotency-Key': uuidv4(), // Required for v2
      }},
      body: JSON.stringify(request),
    }});
    return response.json();
  }}
}}'''
    }
    
    # Generate specific endpoint migration examples
    if "/payments" in from_paths and "/v2/payments" in to_paths:
        examples["create_payment"] = {
            "description": "Migrate payment creation from v1 to v2",
            "before": '''// V1 API - Create payment with cents
const response = await client.createPayment({
  amountCents: 1299, // $12.99 in cents
  currency: "USD"
});

// V1 Response format
const paymentId = response.id;
const status = response.status;
const amountCents = response.amountCents;''',
            "after": '''// V2 API - Create payment with decimal amount
const response = await client.createPayment({
  amount: 12.99, // Direct decimal amount
  currency: "USD"
});

// V2 Response format (field names changed)
const paymentId = response.paymentId; // Changed from "id"
const state = response.state; // Changed from "status"
const amount = response.amount; // Now decimal format'''
        }
        
        examples["get_payment"] = {
            "description": "Migrate payment retrieval from v1 to v2",
            "before": '''// V1 API - Get payment
const response = await fetch(`http://localhost:4010/payments/${{paymentId}}`);
const payment = await response.json();

// V1 field access
const paymentStatus = payment.status;
const amountInCents = payment.amountCents;
const amountInDollars = amountInCents / 100; // Manual conversion''',
            "after": '''// V2 API - Get payment
const response = await fetch(`http://localhost:4011/v2/payments/${{paymentId}}`);
const payment = await response.json();

// V2 field access (updated field names)
const paymentState = payment.state; // Changed from "status"
const amount = payment.amount; // Already in decimal format'''
        }
    
    # Generate error handling example
    examples["error_handling"] = {
        "description": "Update error handling for the new API version",
        "before": '''// V1 Error handling
try {
  const response = await client.createPayment({ amountCents: 1299, currency: "USD" });
  if (response.status === "failed") {
    console.log(`Payment failed: ${{response.id}}`);
  }
} catch (error) {
  console.error(`API error: ${{error}}`);
}''',
        "after": '''// V2 Error handling (updated field names and states)
try {
  const response = await client.createPayment({ amount: 12.99, currency: "USD" });
  if (response.state === "failed") { // Changed from "status"
    console.log(`Payment failed: ${{response.paymentId}}`); // Changed from "id"
  }
} catch (error) {
  console.error(`API error: ${{error}}`);
}'''
    }
    
    return examples
