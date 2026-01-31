"""Configuration for AIATHENA agent."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

from .secrets import get_moltbook_token, get_gemini_api_key

load_dotenv()


@dataclass
class MoltbookConfig:
    """Moltbook API configuration."""
    
    base_url: str = "https://www.moltbook.com/api/v1"
    agent_name: str = "stelly"
    agent_token: str | None = None
    
    # Gemini configuration for autonomous mode
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-pro"
    
    @classmethod
    def from_env(cls) -> "MoltbookConfig":
        """Load configuration from environment variables or GCP Secret Manager."""
        return cls(
            base_url=os.getenv("MOLTBOOK_API_URL", "https://www.moltbook.com/api/v1"),
            agent_name=os.getenv("MOLTBOOK_AGENT_NAME", "AIATHENA"),
            agent_token=get_moltbook_token(),
            gemini_api_key=get_gemini_api_key(),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-pro"),
        )


config = MoltbookConfig.from_env()
