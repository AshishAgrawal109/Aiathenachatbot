from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class SocialPost(BaseModel):
    id: str
    content: str
    author: str
    platform: str
    metadata: Dict[str, Any] = {}

class SocialPlatform(ABC):
    """Abstract base class for social media platforms."""
    
    @abstractmethod
    async def login(self) -> bool:
        """Authenticate with the platform."""
        pass
    
    @abstractmethod
    async def get_profile(self) -> Dict[str, Any]:
        """Get the bot's own profile."""
        pass
    
    @abstractmethod
    async def post(self, content: str, **kwargs) -> Dict[str, Any]:
        """Create a new post."""
        pass
    
    @abstractmethod
    async def get_feed(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Get the platform feed."""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for content."""
        pass

    @abstractmethod
    async def reply(self, post_id: str, content: str) -> Dict[str, Any]:
        """Reply to a post."""
        pass

    @abstractmethod
    async def vote(self, target_id: str, direction: str = "up") -> bool:
        """Vote on content (if applicable)."""
        pass
