"""Secrets management for AIATHENA agent.

Supports:
- Local development: .env file
- GCP deployment: Secret Manager
"""

import os
from functools import lru_cache


# Check if running in GCP (Cloud Run sets these)
IS_GCP = os.getenv("K_SERVICE") is not None or os.getenv("GOOGLE_CLOUD_PROJECT") is not None


def get_secret_from_gcp(secret_id: str, project_id: str | None = None) -> str | None:
    """Fetch a secret from GCP Secret Manager."""
    try:
        from google.cloud import secretmanager
        
        client = secretmanager.SecretManagerServiceClient()
        
        # Get project ID from environment if not provided
        if not project_id:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        
        if not project_id:
            print(f"⚠️ No GCP project ID found for secret: {secret_id}")
            return None
        
        # Build the resource name
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        
        # Access the secret
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    
    except ImportError:
        print("⚠️ google-cloud-secret-manager not installed. Run: pip install google-cloud-secret-manager")
        return None
    except Exception as e:
        print(f"⚠️ Could not fetch secret {secret_id} from Secret Manager: {e}")
        return None


@lru_cache(maxsize=10)
def get_secret(secret_id: str, env_var: str | None = None) -> str | None:
    """Get a secret from environment or GCP Secret Manager.
    
    Priority:
    1. Environment variable (for explicit override)
    2. GCP Secret Manager (always tries, works locally with gcloud auth)
    
    Args:
        secret_id: The secret ID in GCP Secret Manager
        env_var: The environment variable name (defaults to secret_id uppercased with dashes replaced)
    """
    # Determine env var name
    if env_var is None:
        env_var = secret_id.upper().replace("-", "_")
    
    # First check environment variable
    value = os.getenv(env_var)
    if value:
        return value
    
    # Try GCP Secret Manager (works locally with gcloud auth)
    value = get_secret_from_gcp(secret_id)
    if value:
        return value
    
    return None


# Pre-defined secret accessors for AIATHENA
def get_moltbook_token() -> str | None:
    """Get Moltbook agent token.
    
    Checks: MOLTBOOK_AGENT_TOKEN env var, then GCP Secret Manager 'aiathena-moltbook-token'
    """
    return get_secret("aiathena-moltbook-token", "MOLTBOOK_AGENT_TOKEN")


def get_gemini_api_key() -> str | None:
    """Get Gemini API key.
    
    Checks: GEMINI_API_KEY env var, then GCP Secret Manager 'aiathena-gemini-key'
    """
    return get_secret("aiathena-gemini-key", "GEMINI_API_KEY")


def list_available_secrets(project_id: str | None = None) -> list[str]:
    """List all secrets available in GCP Secret Manager."""
    try:
        from google.cloud import secretmanager
        
        client = secretmanager.SecretManagerServiceClient()
        
        if not project_id:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        
        if not project_id:
            return []
        
        parent = f"projects/{project_id}"
        secrets = []
        
        for secret in client.list_secrets(request={"parent": parent}):
            # Extract just the secret name from the full path
            secret_name = secret.name.split("/")[-1]
            secrets.append(secret_name)
        
        return secrets
    except Exception as e:
        print(f"⚠️ Could not list secrets: {e}")
        return []
