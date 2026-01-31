"""AIATHENA MCP Server - Personal agent for Moltbook."""

import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .platforms.moltbook import MoltbookClient
from .config import config

# Initialize the MCP server
server = Server("aiathena")

# Global client instance
client: MoltbookClient | None = None


def get_client() -> MoltbookClient:
    """Get or create the Moltbook client."""
    global client
    if client is None:
        client = MoltbookClient()
    return client


# === Tool Definitions ===

TOOLS = [
    Tool(
        name="moltbook_register",
        description="Register AIATHENA as a new agent on Moltbook. Use this to create an account.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Agent name (default: AIATHENA)",
                    "default": "AIATHENA",
                },
                "bio": {
                    "type": "string",
                    "description": "Agent bio/description",
                },
            },
        },
    ),
    Tool(
        name="moltbook_login",
        description="Login to Moltbook with an existing token.",
        inputSchema={
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "Authentication token",
                },
            },
            "required": ["token"],
        },
    ),
    Tool(
        name="moltbook_get_profile",
        description="Get AIATHENA's current profile on Moltbook.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="moltbook_create_post",
        description="Create a new post on Moltbook.",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Post title",
                },
                "content": {
                    "type": "string",
                    "description": "Post content/body",
                },
                "submolt": {
                    "type": "string",
                    "description": "The submolt (community) to post in. Default: general",
                    "default": "general",
                },
            },
            "required": ["title", "content"],
        },
    ),
    Tool(
        name="moltbook_get_feed",
        description="Get the Moltbook post feed.",
        inputSchema={
            "type": "object",
            "properties": {
                "sort": {
                    "type": "string",
                    "enum": ["hot", "new", "top"],
                    "description": "Sort order (default: hot)",
                    "default": "hot",
                },
                "page": {
                    "type": "integer",
                    "description": "Page number",
                    "default": 1,
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of posts per page",
                    "default": 20,
                },
            },
        },
    ),
    Tool(
        name="moltbook_get_post",
        description="Get a specific post by ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "post_id": {
                    "type": "string",
                    "description": "The post ID",
                },
            },
            "required": ["post_id"],
        },
    ),
    Tool(
        name="moltbook_search",
        description="Semantic search for posts on Moltbook.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (semantic search)",
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="moltbook_create_comment",
        description="Create a comment on a post.",
        inputSchema={
            "type": "object",
            "properties": {
                "post_id": {
                    "type": "string",
                    "description": "The post ID to comment on",
                },
                "content": {
                    "type": "string",
                    "description": "Comment content",
                },
            },
            "required": ["post_id", "content"],
        },
    ),
    Tool(
        name="moltbook_get_comments",
        description="Get comments for a post.",
        inputSchema={
            "type": "object",
            "properties": {
                "post_id": {
                    "type": "string",
                    "description": "The post ID",
                },
                "page": {
                    "type": "integer",
                    "description": "Page number",
                    "default": 1,
                },
            },
            "required": ["post_id"],
        },
    ),
    Tool(
        name="moltbook_upvote",
        description="Upvote a post or comment.",
        inputSchema={
            "type": "object",
            "properties": {
                "target_type": {
                    "type": "string",
                    "enum": ["post", "comment"],
                    "description": "Type of content to upvote",
                },
                "target_id": {
                    "type": "string",
                    "description": "ID of the post or comment",
                },
            },
            "required": ["target_type", "target_id"],
        },
    ),
    Tool(
        name="moltbook_downvote",
        description="Downvote a post or comment.",
        inputSchema={
            "type": "object",
            "properties": {
                "target_type": {
                    "type": "string",
                    "enum": ["post", "comment"],
                    "description": "Type of content to downvote",
                },
                "target_id": {
                    "type": "string",
                    "description": "ID of the post or comment",
                },
            },
            "required": ["target_type", "target_id"],
        },
    ),
    Tool(
        name="moltbook_get_agent",
        description="Get another agent's profile by handle.",
        inputSchema={
            "type": "object",
            "properties": {
                "handle": {
                    "type": "string",
                    "description": "The agent's handle (username)",
                },
            },
            "required": ["handle"],
        },
    ),
    Tool(
        name="moltbook_follow",
        description="Follow another agent.",
        inputSchema={
            "type": "object",
            "properties": {
                "handle": {
                    "type": "string",
                    "description": "The agent handle to follow",
                },
            },
            "required": ["handle"],
        },
    ),
    Tool(
        name="moltbook_unfollow",
        description="Unfollow an agent.",
        inputSchema={
            "type": "object",
            "properties": {
                "handle": {
                    "type": "string",
                    "description": "The agent handle to unfollow",
                },
            },
            "required": ["handle"],
        },
    ),
    Tool(
        name="moltbook_get_submolts",
        description="Get available submolts (communities).",
        inputSchema={"type": "object", "properties": {}},
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Moltbook tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a Moltbook tool."""
    moltbook = get_client()
    
    try:
        result = await _execute_tool(moltbook, name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        return [TextContent(type="text", text=json.dumps({"error": error_msg}))]


async def _execute_tool(moltbook: MoltbookClient, name: str, args: dict) -> dict:
    """Execute a specific tool and return the result."""
    
    match name:
        case "moltbook_register":
            agent_name = args.get("name", config.agent_name)
            bio = args.get("bio")
            return await moltbook.register(agent_name, bio)
        
        case "moltbook_login":
            return await moltbook.login(args["token"])
        
        case "moltbook_get_profile":
            return await moltbook.get_me()
        
        case "moltbook_create_post":
            return await moltbook.create_post(
                args["title"], 
                args["content"],
                args.get("submolt", "general")
            )
        
        case "moltbook_get_feed":
            return await moltbook.get_feed(
                sort=args.get("sort", "hot"),
                limit=args.get("limit", 20),
                page=args.get("page", 1),
            )
        
        case "moltbook_get_post":
            return await moltbook.get_post(args["post_id"])
        
        case "moltbook_search":
            return await moltbook.search(args["query"])
        
        case "moltbook_create_comment":
            return await moltbook.create_comment(args["post_id"], args["content"])
        
        case "moltbook_get_comments":
            return await moltbook.get_comments(args["post_id"], args.get("page", 1))
        
        case "moltbook_upvote":
            target_type = args["target_type"]
            target_id = args["target_id"]
            
            if target_type == "post":
                return await moltbook.upvote_post(target_id)
            else:
                return await moltbook.upvote_comment(target_id)
        
        case "moltbook_downvote":
            target_type = args["target_type"]
            target_id = args["target_id"]
            
            if target_type == "post":
                return await moltbook.downvote_post(target_id)
            else:
                return await moltbook.downvote_comment(target_id)
        
        case "moltbook_get_agent":
            return await moltbook.get_agent(args["handle"])
        
        case "moltbook_follow":
            return await moltbook.follow_agent(args["handle"])
        
        case "moltbook_unfollow":
            return await moltbook.unfollow_agent(args["handle"])
        
        case "moltbook_get_submolts":
            return await moltbook.get_submolts()
        
        case _:
            return {"error": f"Unknown tool: {name}"}


def main():
    """Run the AIATHENA MCP server."""
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    
    asyncio.run(run())


if __name__ == "__main__":
    main()
