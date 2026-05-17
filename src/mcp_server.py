"""
MCP Server for Database Comparison Tools.
Exposes database quality analysis tools as an MCP server.
Can be used with any MCP-compatible client (Claude, etc).
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from tools import (
    get_missing_rows,
    get_mismatched_rows,
    get_quality_score,
    run_full_comparison,
    export_report
)

# Setup logging to stderr
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
logger = logging.getLogger(__name__)

# Create the server
server = Server("database-quality-server")

# ---------- Tool Definitions ----------
TOOLS = [
    Tool(
        name="get_missing_rows",
        description="Get all rows that exist in Production DB but are missing in Staging DB. Returns count, percentage, and list of missing rows.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    Tool(
        name="get_mismatched_rows",
        description="Get all rows with data differences between Production and Staging databases. Returns count, percentage, and detailed comparisons.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    Tool(
        name="get_quality_score",
        description="Get overall data quality score and metrics comparing the two databases. Returns quality score, record counts, and health statistics.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    Tool(
        name="run_full_comparison",
        description="Run a complete comparison between Production and Staging databases. Combines all analysis and provides recommendations.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    Tool(
        name="export_report",
        description="Export the full comparison report to a JSON file. Optional: specify output file path.",
        inputSchema={
            "type": "object",
            "properties": {
                "output_file": {
                    "type": "string",
                    "description": "Path where to save the JSON report. If not provided, uses default location in data folder."
                }
            },
            "required": []
        }
    )
]


# ---------- Tool Handlers ----------
async def handle_get_missing_rows(arguments: Dict[str, Any]) -> str:
    """Handle get_missing_rows tool call."""
    try:
        result = get_missing_rows()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


async def handle_get_mismatched_rows(arguments: Dict[str, Any]) -> str:
    """Handle get_mismatched_rows tool call."""
    try:
        result = get_mismatched_rows()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


async def handle_get_quality_score(arguments: Dict[str, Any]) -> str:
    """Handle get_quality_score tool call."""
    try:
        result = get_quality_score()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


async def handle_run_full_comparison(arguments: Dict[str, Any]) -> str:
    """Handle run_full_comparison tool call."""
    try:
        result = run_full_comparison()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


async def handle_export_report(arguments: Dict[str, Any]) -> str:
    """Handle export_report tool call."""
    try:
        output_file = arguments.get("output_file", None)
        result = export_report(output_file)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# Tool handler mapping
TOOL_HANDLERS = {
    "get_missing_rows": handle_get_missing_rows,
    "get_mismatched_rows": handle_get_mismatched_rows,
    "get_quality_score": handle_get_quality_score,
    "run_full_comparison": handle_run_full_comparison,
    "export_report": handle_export_report,
}


# ---------- MCP Server Handlers ----------
@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    if name not in TOOL_HANDLERS:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unknown tool: {name}",
                    "available_tools": list(TOOL_HANDLERS.keys())
                })
            )
        ]
    
    handler = TOOL_HANDLERS[name]
    result = await handler(arguments)
    
    return [
        TextContent(
            type="text",
            text=result
        )
    ]


# ---------- Main ----------
def main():
    """Run the MCP server."""
    logger.info("Starting Database Quality MCP Server...")
    logger.info("Available tools:")
    for tool in TOOLS:
        logger.info(f"  - {tool.name}: {tool.description}")
    logger.info("Server ready. Waiting for connections...")
    
    mcp.server.stdio.stdio_server(server)


if __name__ == "__main__":
    main()
