"""Moltbook implementation of SocialPlatform."""

import httpx
from typing import Any, Dict, List
from .base import SocialPlatform
from ..config import MoltbookConfig, config

class MoltbookClient(SocialPlatform):
    """Moltbook platform integration."""
    
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
                timeout=httpx.Timeout(60.0, connect=10.0),
                follow_redirects=True,
                http2=False,  # Force HTTP/1.1 for compatibility
            )
        else:
            self._client.headers.update(self.headers)
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make generic request."""
        client = await self._get_client()
        response = await client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        if response.status_code == 204:
            return {"success": True}
        return response.json()

    # --- SocialPlatform Implementation ---

    async def login(self, token: str | None = None) -> bool:
        if token:
            self._api_key = token
        return True # Moltbook uses token auth, no session login

    async def get_profile(self) -> Dict[str, Any]:
        return await self._request("GET", "/agents/me")
    
    async def post(self, content: str, title: str | None = None, submolt: str = "general", **kwargs) -> Dict[str, Any]:
        # Moltbook requires title for posts
        data = {
            "content": content,
            "submolt": submolt,
            "title": title or "Post from AIATHENA"
        }
        return await self._request("POST", "/posts", json=data)
    
    async def get_feed(self, limit: int = 10, sort: str = "hot", page: int = 1, **kwargs) -> List[Dict[str, Any]]:
        params = {"limit": limit, "sort": sort, "page": page}
        response = await self._request("GET", "/posts", params=params)
        return response # Moltbook returns list typically
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        return await self._request("GET", "/search", params={"q": query, "limit": limit})
    
    async def reply(self, post_id: str, content: str) -> Dict[str, Any]:
        return await self._request("POST", f"/posts/{post_id}/comments", json={"content": content})
    
    async def vote(self, target_id: str, direction: str = "up", target_type: str = "post") -> bool:
        endpoint = f"/{target_type}s/{target_id}/{direction}vote" # e.g. /posts/123/upvote
        try:
            await self._request("POST", endpoint)
            return True
        except:
            return False

    # --- Specific Moltbook Methods (legacy support) ---
    
    async def register(self, name: str, description: str | None = None) -> dict[str, Any]:
        data = {"name": name}
        if description:
            data["description"] = description
        result = await self._request("POST", "/agents/register", json=data)
        if result.get("agent", {}).get("api_key"):
            self._api_key = result["agent"]["api_key"]
        return result
    
    async def create_post(self, title: str, content: str, submolt: str = "general") -> dict[str, Any]:
        return await self.post(content=content, title=title, submolt=submolt)

    async def get_post(self, post_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/posts/{post_id}")
    
    async def upvote_post(self, post_id: str) -> dict[str, Any]:
        await self.vote(post_id, "up", "post")
        return {"success": True}
        
    async def downvote_post(self, post_id: str) -> dict[str, Any]:
        await self.vote(post_id, "down", "post")
        return {"success": True}
    
    async def upvote_comment(self, comment_id: str) -> dict[str, Any]:
        await self.vote(comment_id, "up", "comment")
        return {"success": True}

    async def downvote_comment(self, comment_id: str) -> dict[str, Any]:
        await self.vote(comment_id, "down", "comment")
        return {"success": True}

    async def create_comment(self, post_id: str, content: str) -> dict[str, Any]:
        return await self.reply(post_id, content)

    async def get_comments(self, post_id: str, page: int = 1) -> dict[str, Any]:
        return await self._request("GET", f"/posts/{post_id}/comments", params={"page": page})

    async def get_agent(self, agent_name: str) -> dict[str, Any]:
        return await self._request("GET", "/agents/profile", params={"name": agent_name})

    async def follow_agent(self, agent_name: str) -> dict[str, Any]:
        return await self._request("POST", f"/agents/{agent_name}/follow")

    async def unfollow_agent(self, agent_name: str) -> dict[str, Any]:
        return await self._request("DELETE", f"/agents/{agent_name}/follow")

    async def get_submolts(self) -> dict[str, Any]:
        return await self._request("GET", "/submolts")
