"""CBM sidecar MCP server — context, rename, route_map tools."""
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cbm-sidecar")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="context",
            description="360-degree view of a code symbol. Shows incoming/outgoing references.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Symbol name"},
                    "file_path": {"type": "string", "description": "Optional disambiguation hint"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="rename",
            description="Multi-file coordinated rename using graph + text search.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol_name": {"type": "string"},
                    "new_name": {"type": "string"},
                    "file_path": {"type": "string"},
                    "dry_run": {"type": "boolean", "default": True}
                },
                "required": ["symbol_name", "new_name"]
            }
        ),
        Tool(
            name="route_map",
            description="API route handler to consumer mapping. Heuristic-based.",
            inputSchema={
                "type": "object",
                "properties": {
                    "route": {"type": "string", "description": "Optional route filter"}
                }
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    return [TextContent(type="text", text=f"Tool '{name}' not yet implemented. Arguments: {arguments}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
