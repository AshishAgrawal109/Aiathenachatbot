"""Moltbook API client for AIATHENA agent."""

import httpx
from typing import Any
from pydantic import BaseModel

from .config import MoltbookConfig, config


class AgentProfile(BaseModel):
    """Agent profile model."""
    name: str
    description: str | None = None
    karma: int = 0
    created_at: str | None = None


class Post(BaseModel):
    """Post model."""
    id: str
    title: str
    content: str | None = None
    url: str | None = None
    submolt: str = "general"
    upvotes: int = 0
    downvotes: int = 0
    created_at: str | None = None


class Comment(BaseModel):
    """Comment model."""
    id: str
    content: str
    post_id: str
    upvotes: int = 0
    downvotes: int = 0
    created_at: str | None = None


class MoltbookClient:
    """HTTP client for Moltbook API."""
    
    def __init__(self, cfg: MoltbookConfig | None = None):
        self.config = cfg or config
        self._client: httpx.AsyncClient | None = None
        self._api_key: str | None = self.config.agent_token
    
    @property
    def headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=self.headers,
                timeout=30.0,
            )
        else:
            # Update headers in case token changed (e.g., after login)
            self._client.headers.update(self.headers)
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: dict | None = None,
        params: dict | None = None,
    ) -> dict[str, Any]:
        """Make an API request."""
        client = await self._get_client()
        
        kwargs: dict[str, Any] = {}
        if data:
            kwargs["json"] = data
        if params:
            kwargs["params"] = params
        
        response = await client.request(method, endpoint, **kwargs)
        
        # Handle errors with response body
        if response.status_code >= 400:
            try:
                error_body = response.json()
                error_msg = error_body.get("error", str(response.status_code))
                hint = error_body.get("hint", "")
                retry_after = error_body.get("retry_after_minutes")
                full_error = f"{response.status_code}: {error_msg}"
                if hint:
                    full_error += f" ({hint})"
                if retry_after:
                    full_error += f" [retry in {retry_after}min]"
                raise Exception(full_error)
            except Exception as e:
                if "status_code" not in str(e):
                    response.raise_for_status()
                raise
        
        if response.status_code == 204:
            return {"success": True}
        return response.json()
    
    # === Authentication ===
    
    async def register(self, name: str, description: str | None = None) -> dict[str, Any]:
        """Register a new agent on Moltbook."""
        data = {"name": name}
        if description:
            data["description"] = description
        result = await self._request("POST", "/agents/register", data)
        # Save the API key if returned
        if result.get("agent", {}).get("api_key"):
            self._api_key = result["agent"]["api_key"]
        return result
    
    async def login(self, api_key: str) -> dict[str, Any]:
        """Login with an existing API key."""
        self._api_key = api_key
        return await self.get_me()
    
    async def get_me(self) -> dict[str, Any]:
        """Get current agent's profile."""
        return await self._request("GET", "/agents/me")
    
    async def get_status(self) -> dict[str, Any]:
        """Check agent claim status."""
        return await self._request("GET", "/agents/status")
    
    # === Posts ===
    
    async def create_post(self, title: str, content: str, submolt: str = "general") -> dict[str, Any]:
        """Create a new post."""
        return await self._request("POST", "/posts", {
            "submolt": submolt,
            "title": title,
            "content": content,
        })
    
    async def get_post(self, post_id: str) -> dict[str, Any]:
        """Get a specific post by ID."""
        return await self._request("GET", f"/posts/{post_id}")
    
    async def get_feed(self, sort: str = "hot", limit: int = 25, page: int = 1, submolt: str | None = None) -> dict[str, Any]:
        """Get the post feed."""
        params = {"sort": sort, "limit": limit, "page": page}
        if submolt:
            params["submolt"] = submolt
        return await self._request("GET", "/posts", params=params)
    
    async def get_personalized_feed(self, sort: str = "hot", limit: int = 25) -> dict[str, Any]:
        """Get personalized feed (from subscribed submolts and followed agents)."""
        return await self._request("GET", "/feed", params={"sort": sort, "limit": limit})
    
    async def search(self, query: str, search_type: str = "all", limit: int = 20) -> dict[str, Any]:
        """Semantic search for posts and comments."""
        return await self._request("GET", "/search", params={
            "q": query,
            "type": search_type,
            "limit": limit,
        })
    
    # === Voting ===
    
    async def upvote_post(self, post_id: str) -> dict[str, Any]:
        """Upvote a post."""
        return await self._request("POST", f"/posts/{post_id}/upvote")
    
    async def downvote_post(self, post_id: str) -> dict[str, Any]:
        """Downvote a post."""
        return await self._request("POST", f"/posts/{post_id}/downvote")
    
    async def upvote_comment(self, comment_id: str) -> dict[str, Any]:
        """Upvote a comment."""
        return await self._request("POST", f"/comments/{comment_id}/upvote")
    
    async def downvote_comment(self, comment_id: str) -> dict[str, Any]:
        """Downvote a comment."""
        return await self._request("POST", f"/comments/{comment_id}/downvote")
    
    # === Comments ===
    
    async def create_comment(self, post_id: str, content: str) -> dict[str, Any]:
        """Create a comment on a post."""
        return await self._request("POST", f"/posts/{post_id}/comments", {"content": content})
    
    async def get_comments(self, post_id: str, page: int = 1) -> dict[str, Any]:
        """Get comments for a post."""
        return await self._request("GET", f"/posts/{post_id}/comments", params={"page": page})
    
    # === Agents ===
    
    async def get_agent(self, agent_name: str) -> dict[str, Any]:
        """Get an agent's profile by name."""
        return await self._request("GET", "/agents/profile", params={"name": agent_name})
    
    async def follow_agent(self, agent_name: str) -> dict[str, Any]:
        """Follow another agent."""
        return await self._request("POST", f"/agents/{agent_name}/follow")
    
    async def unfollow_agent(self, agent_name: str) -> dict[str, Any]:
        """Unfollow an agent."""
        return await self._request("DELETE", f"/agents/{agent_name}/follow")
    
    # === Submolts (Communities) ===
    
    async def get_submolts(self) -> dict[str, Any]:
        """List all submolts."""
        return await self._request("GET", "/submolts")
    
    async def get_submolt(self, name: str) -> dict[str, Any]:
        """Get submolt info."""
        return await self._request("GET", f"/submolts/{name}")
    
    async def subscribe_submolt(self, name: str) -> dict[str, Any]:
        """Subscribe to a submolt."""
        return await self._request("POST", f"/submolts/{name}/subscribe")
    
    async def unsubscribe_submolt(self, name: str) -> dict[str, Any]:
        """Unsubscribe from a submolt."""
        return await self._request("DELETE", f"/submolts/{name}/subscribe")
