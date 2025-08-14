#!/usr/bin/env python3
"""
API migration guide generation module.
This module contains functions for generating comprehensive migration guides and documentation.
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List
from .migration_analyzer import (
    parse_openapi_definition,
    analyze_api_migration_fast,
    generate_typescript_migration_examples
)

logger = logging.getLogger("agentics-mcp.mermaid.migration_guide")


async def generate_api_migration_plan_internal(from_api: str, to_api: str, base_url: str = None) -> str:
    """Generate a detailed migration plan from one API version to another with Python code examples.
    
    Args:
        from_api: The name of the source API to migrate from
        to_api: The name of the target API to migrate to
        base_url: Optional base URL override for Backstage API
        
    Returns:
        Detailed migration plan with Python code examples as JSON string, or error message if failed
    """
    try:
        logger.info(f"Generating API migration plan: {from_api} -> {to_api}")
        
        # Import here to avoid circular imports
        from api_client import fetch_backstage_api_entity
        
        # Fetch both API entities with timeout and error handling
        try:
            from_api_task = asyncio.create_task(
                asyncio.wait_for(fetch_backstage_api_entity(from_api), timeout=10.0)
            )
            to_api_task = asyncio.create_task(
                asyncio.wait_for(fetch_backstage_api_entity(to_api), timeout=10.0)
            )
            
            from_api_data, to_api_data = await asyncio.gather(from_api_task, to_api_task)
        except asyncio.TimeoutError:
            return json.dumps({
                "error": "API fetch timeout",
                "message": "Timeout while fetching API entities from Backstage. Please try again.",
                "from_api": from_api,
                "to_api": to_api
            }, indent=2)
        
        # Parse API data
        try:
            from_api_info = json.loads(from_api_data)
            to_api_info = json.loads(to_api_data)
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": "API parsing error",
                "message": f"Failed to parse API data: {str(e)}",
                "from_api": from_api,
                "to_api": to_api
            }, indent=2)
        
        # Check if APIs exist and have proper structure
        if "error" in from_api_info:
            return json.dumps({
                "error": "Source API not found",
                "message": f"Could not find source API '{from_api}' in Backstage catalog. Please verify the API name.",
                "from_api": from_api,
                "to_api": to_api
            }, indent=2)
        
        if "error" in to_api_info:
            return json.dumps({
                "error": "Target API not found", 
                "message": f"Could not find target API '{to_api}' in Backstage catalog. Please verify the API name.",
                "from_api": from_api,
                "to_api": to_api
            }, indent=2)
        
        # Validate that both APIs have the same provider (critical for migration validity)
        from_relations = from_api_info.get("relations", [])
        to_relations = to_api_info.get("relations", [])
        
        from_provider = None
        to_provider = None
        
        for relation in from_relations:
            if relation.get("type") == "apiProvidedBy":
                from_provider = relation.get("targetRef", "").replace("component:default/", "")
                break
        
        for relation in to_relations:
            if relation.get("type") == "apiProvidedBy":
                to_provider = relation.get("targetRef", "").replace("component:default/", "")
                break
        
        # Strict validation: Both APIs must have the same provider
        if not from_provider or not to_provider:
            return json.dumps({
                "error": "Missing API provider relations",
                "message": "Both APIs must have 'apiProvidedBy' relations defined in Backstage. Please ask the architects to ensure proper relations are established before attempting migration.",
                "from_api": from_api,
                "to_api": to_api,
                "from_provider": from_provider,
                "to_provider": to_provider,
                "recommendation": "Contact the system architects to establish proper API provider relations in Backstage catalog."
            }, indent=2)
        
        if from_provider != to_provider:
            return json.dumps({
                "error": "API provider mismatch",
                "message": f"Migration not allowed: APIs are provided by different services. Source API '{from_api}' is provided by '{from_provider}' while target API '{to_api}' is provided by '{to_provider}'. Please ask the architects to verify this is a valid migration path.",
                "from_api": from_api,
                "to_api": to_api,
                "from_provider": from_provider,
                "to_provider": to_provider,
                "recommendation": "Contact the system architects to confirm this cross-service API migration is intentional and properly designed."
            }, indent=2)
        
        # Extract API specifications
        from_spec = from_api_info.get("spec", {})
        to_spec = to_api_info.get("spec", {})
        
        from_definition = from_spec.get("definition", "")
        to_definition = to_spec.get("definition", "")
        
        # Parse OpenAPI definitions
        from_openapi = parse_openapi_definition(from_definition)
        to_openapi = parse_openapi_definition(to_definition)
        
        if not from_openapi or not to_openapi:
            return json.dumps({
                "error": "OpenAPI parsing error",
                "message": "Could not parse OpenAPI definitions from one or both APIs. Migration analysis requires valid OpenAPI specifications.",
                "from_api": from_api,
                "to_api": to_api
            }, indent=2)
        
        # Generate comprehensive migration analysis (optimized - no additional API calls)
        migration_analysis = analyze_api_migration_fast(from_openapi, to_openapi, from_api, to_api)
        
        # Find consumers of the source API from existing relations data
        consumers = []
        for relation in from_relations:
            if relation.get("type") == "apiConsumedBy":
                consumer = relation.get("targetRef", "").replace("component:default/", "")
                if consumer:
                    consumers.append(consumer)
        
        # Generate TypeScript code examples
        migration_analysis["typescript_examples"] = generate_typescript_migration_examples(
            from_openapi, to_openapi, from_api, to_api
        )
        
        # Generate Markdown migration guide (optimized)
        markdown_guide = generate_markdown_migration_guide_fast(
            from_api, to_api, from_provider, consumers, 
            from_openapi, to_openapi, from_spec, to_spec, 
            migration_analysis
        )
        
        logger.info(f"Successfully generated migration plan: {from_api} -> {to_api}")
        return markdown_guide
        
    except Exception as e:
        logger.error(f"Failed to generate migration plan {from_api} -> {to_api}: {e}", exc_info=True)
        return json.dumps({
            "error": "Migration plan generation error",
            "message": f"Failed to generate migration plan: {str(e)}",
            "from_api": from_api,
            "to_api": to_api
        }, indent=2)


def generate_markdown_migration_guide_fast(from_api: str, to_api: str, provider_service: str, consumers: List[str], 
                                          from_openapi: Dict, to_openapi: Dict, from_spec: Dict, to_spec: Dict, 
                                          migration_analysis: Dict) -> str:
    """Generate a human-readable Markdown migration guide (fast version)."""
    
    # Get API version info
    from_version = from_openapi.get("info", {}).get("version", "unknown")
    to_version = to_openapi.get("info", {}).get("version", "unknown")
    from_description = from_openapi.get("info", {}).get("description", "")
    to_description = to_openapi.get("info", {}).get("description", "")
    
    markdown_lines = [
        f"# API Migration Guide: {from_api} → {to_api}",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Migration Complexity:** {migration_analysis['complexity'].upper()}",
        f"**Estimated Effort:** {migration_analysis['estimated_effort']}",
        f"**Breaking Changes:** {len(migration_analysis['breaking_changes'])}",
        "",
        "## Migration Summary",
        "",
        f"This guide provides step-by-step instructions for migrating from `{from_api}` to `{to_api}`.",
        "",
        f"- **Source API:** `{from_api}` (v{from_version}) - {from_spec.get('lifecycle', 'unknown')}",
        f"- **Target API:** `{to_api}` (v{to_version}) - {to_spec.get('lifecycle', 'unknown')}",
        f"- **Provider Service:** `{provider_service}`",
        f"- **Affected Consumers:** {', '.join([f'`{c}`' for c in consumers]) if consumers else 'None'}",
        "",
        "### Validation Status",
        "",
        "- **Backstage Relations Verified:** Both APIs have proper `apiProvidedBy` relations",
        f"- **Same Provider Confirmed:** Both APIs are provided by `{provider_service}`",
        "- **Migration Path Valid:** This is a safe migration between API versions",
        "",
        "## API Comparison",
        "",
        "| Aspect | Source API | Target API |",
        "|--------|------------|------------|",
        f"| **Name** | `{from_api}` | `{to_api}` |",
        f"| **Version** | {from_version} | {to_version} |",
        f"| **Lifecycle** | {from_spec.get('lifecycle', 'unknown')} | {to_spec.get('lifecycle', 'unknown')} |",
        f"| **Description** | {from_description} | {to_description} |",
        "",
    ]
    
    # Add breaking changes section
    if migration_analysis["breaking_changes"]:
        markdown_lines.extend([
            "## Breaking Changes",
            "",
            "The following breaking changes require code updates:",
            "",
        ])
        
        for i, change in enumerate(migration_analysis["breaking_changes"], 1):
            markdown_lines.extend([
                f"### {i}. {change['description']}",
                "",
                f"- **Type:** {change['type'].replace('_', ' ').title()}",
                f"- **Impact:** {change['impact'].title()}",
                f"- **Endpoint:** `{change.get('endpoint', 'N/A')}`",
                "",
            ])
    
    # Add new features section
    if migration_analysis["new_features"]:
        markdown_lines.extend([
            "## New Features",
            "",
            "The target API introduces the following new features:",
            "",
        ])
        
        for feature in migration_analysis["new_features"]:
            markdown_lines.append(f"- {feature}")
        
        markdown_lines.append("")
    
    # Add removed features section
    if migration_analysis["removed_features"]:
        markdown_lines.extend([
            "## Removed Features",
            "",
            "The following features have been removed and are no longer available:",
            "",
        ])
        
        for feature in migration_analysis["removed_features"]:
            markdown_lines.append(f"- {feature}")
        
        markdown_lines.append("")
    
    # Add migration steps
    markdown_lines.extend([
        "## Migration Steps",
        "",
        "Follow these steps to complete the migration:",
        "",
    ])
    
    for step in migration_analysis["migration_steps"]:
        step_num = step["step"]
        markdown_lines.extend([
            f"### Step {step_num}: {step['title']}",
            "",
            f"**Description:** {step['description']}",
            "",
            f"**Action:** {step['action']}",
            "",
        ])
    
    # Add TypeScript code examples
    markdown_lines.extend([
        "## TypeScript Code Examples",
        "",
        "Here are specific code examples to help with the migration:",
        "",
    ])
    
    for example_name, example_data in migration_analysis["typescript_examples"].items():
        markdown_lines.extend([
            f"### {example_name.replace('_', ' ').title()}",
            "",
            f"**{example_data['description']}**",
            "",
            "#### Before (Old API):",
            "",
            "```typescript",
            example_data["before"],
            "```",
            "",
            "#### After (New API):",
            "",
            "```typescript",
            example_data["after"],
            "```",
            "",
        ])
    
    return "\n".join(markdown_lines)


def generate_migration_summary(from_api: str, to_api: str, migration_analysis: Dict) -> Dict:
    """Generate a concise migration summary for quick reference.
    
    Args:
        from_api: Source API name
        to_api: Target API name
        migration_analysis: Full migration analysis
        
    Returns:
        Dictionary containing migration summary
    """
    return {
        "migration_path": f"{from_api} → {to_api}",
        "complexity": migration_analysis["complexity"],
        "estimated_effort": migration_analysis["estimated_effort"],
        "breaking_changes_count": len(migration_analysis["breaking_changes"]),
        "new_features_count": len(migration_analysis["new_features"]),
        "removed_features_count": len(migration_analysis["removed_features"]),
        "migration_steps_count": len(migration_analysis["migration_steps"]),
        "has_code_examples": len(migration_analysis["typescript_examples"]) > 0,
        "risk_level": _assess_migration_risk(migration_analysis),
        "recommended_timeline": _suggest_migration_timeline(migration_analysis)
    }


def _assess_migration_risk(migration_analysis: Dict) -> str:
    """Assess the risk level of the migration based on breaking changes."""
    breaking_changes = migration_analysis["breaking_changes"]
    
    if not breaking_changes:
        return "low"
    
    high_impact_changes = [c for c in breaking_changes if c.get("impact") == "high"]
    
    if len(high_impact_changes) >= 3:
        return "high"
    elif len(high_impact_changes) >= 1 or len(breaking_changes) >= 5:
        return "medium"
    else:
        return "low"


def _suggest_migration_timeline(migration_analysis: Dict) -> str:
    """Suggest a migration timeline based on complexity and risk."""
    complexity = migration_analysis["complexity"]
    breaking_changes_count = len(migration_analysis["breaking_changes"])
    
    if complexity == "high" or breaking_changes_count >= 5:
        return "2-3 weeks (including testing and rollback planning)"
    elif complexity == "medium" or breaking_changes_count >= 2:
        return "1-2 weeks (including thorough testing)"
    else:
        return "3-5 days (with basic testing)"


def generate_migration_checklist(migration_analysis: Dict) -> List[Dict]:
    """Generate a checklist for migration tasks.
    
    Args:
        migration_analysis: Full migration analysis
        
    Returns:
        List of checklist items with completion status
    """
    checklist = []
    
    # Pre-migration tasks
    checklist.extend([
        {
            "category": "Pre-Migration",
            "task": "Review all breaking changes",
            "completed": False,
            "priority": "high"
        },
        {
            "category": "Pre-Migration", 
            "task": "Identify affected code areas",
            "completed": False,
            "priority": "high"
        },
        {
            "category": "Pre-Migration",
            "task": "Create migration branch",
            "completed": False,
            "priority": "medium"
        }
    ])
    
    # Implementation tasks based on breaking changes
    for change in migration_analysis["breaking_changes"]:
        if change["type"] == "endpoint_removed":
            checklist.append({
                "category": "Implementation",
                "task": f"Handle removed endpoint: {change['endpoint']}",
                "completed": False,
                "priority": "high"
            })
        elif change["type"] == "parameter_removed":
            checklist.append({
                "category": "Implementation",
                "task": f"Remove parameter '{change['parameter']}' from {change['endpoint']}",
                "completed": False,
                "priority": "medium"
            })
    
    # Testing tasks
    checklist.extend([
        {
            "category": "Testing",
            "task": "Update unit tests",
            "completed": False,
            "priority": "high"
        },
        {
            "category": "Testing",
            "task": "Run integration tests",
            "completed": False,
            "priority": "high"
        },
        {
            "category": "Testing",
            "task": "Perform manual testing",
            "completed": False,
            "priority": "medium"
        }
    ])
    
    # Deployment tasks
    checklist.extend([
        {
            "category": "Deployment",
            "task": "Deploy to staging environment",
            "completed": False,
            "priority": "high"
        },
        {
            "category": "Deployment",
            "task": "Monitor staging for issues",
            "completed": False,
            "priority": "high"
        },
        {
            "category": "Deployment",
            "task": "Deploy to production",
            "completed": False,
            "priority": "high"
        },
        {
            "category": "Deployment",
            "task": "Monitor production metrics",
            "completed": False,
            "priority": "high"
        }
    ])
    
    return checklist
