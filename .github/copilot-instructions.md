# Stelly Agent - Copilot Instructions

## Project Overview
Stelly is a personal AI agent for the Moltbook social network (https://www.moltbook.com). It's built as an MCP (Model Context Protocol) server that allows AI assistants to interact with Moltbook.

## Technology Stack
- **Language**: Python 3.11+
- **Framework**: MCP SDK for Python
- **HTTP Client**: httpx (async)
- **Configuration**: pydantic, python-dotenv

## Project Structure
```
stelly/
├── src/stelly/
│   ├── __init__.py      # Package init
│   ├── config.py        # Configuration management
│   ├── client.py        # Moltbook API client
│   └── server.py        # MCP server implementation
├── .env.example         # Environment template
├── pyproject.toml       # Project dependencies
└── .vscode/mcp.json     # VS Code MCP configuration
```

## Available MCP Tools
- `moltbook_register` - Register as a new agent
- `moltbook_login` - Login with token
- `moltbook_get_profile` - Get Stelly's profile
- `moltbook_create_post` - Create a post
- `moltbook_get_feed` - Browse the feed
- `moltbook_get_post` - Get a specific post
- `moltbook_search` - Search for posts
- `moltbook_create_comment` - Comment on a post
- `moltbook_get_comments` - Get post comments
- `moltbook_vote` - Vote on posts/comments
- `moltbook_get_agent` - View agent profiles
- `moltbook_follow` - Follow/unfollow agents
- `moltbook_get_notifications` - Get notifications
- `moltbook_heartbeat` - Send activity heartbeat

## Development Commands
```bash
# Install dependencies
uv sync

# Run the MCP server
uv run stelly

# Run in development mode
uv run python -m stelly.server
```

## API Reference
- Moltbook API: https://www.moltbook.com/api
- MCP SDK: https://github.com/modelcontextprotocol/python-sdk
