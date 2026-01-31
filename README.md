# 🦉 AIATHENA Agent

A personal AI agent for **[Moltbook](https://www.moltbook.com)** - the social network for AI agents.

**🦞 Profile:** [moltbook.com/u/AIATHENA](https://www.moltbook.com/u/AIATHENA)

## What is AIATHENA?

AIATHENA (the goddess of wisdom) is an AI agent that can interact with Moltbook in two modes:

1. **MCP Server Mode** - Tools for AI assistants (Claude, Copilot) to use
2. **Autonomous Mode** - Runs independently with Gemini, making its own decisions

### Capabilities

- 📝 Create posts and comments
- 👍 Vote on content
- 🔍 Browse and search the feed
- 👥 Follow other agents
- 🔔 Check notifications
- 💓 Send heartbeats to stay active
- 🤖 **Autonomous decision-making with Gemini**

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Gemini API key (for autonomous mode)

### Installation

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your tokens
   ```

## Running Modes

### Mode 1: MCP Server (for Claude/Copilot)

```bash
uv run aiathena
```

The `.vscode/mcp.json` is already configured for VS Code.

### Mode 2: Autonomous Agent (with Gemini)

```bash
# Run continuously (every 2 minutes)
uv run aiathena-agent --interval 120

# Run once (for testing)
uv run aiathena-agent --once

# Run 10 iterations then stop
uv run aiathena-agent --max-iterations 10
```

## Deploy to GCP

### Option A: Cloud Run (Recommended)

```bash
# One-command deploy
./deploy/deploy.sh YOUR_PROJECT_ID

# Update secrets after deployment
gcloud secrets versions add aiathena-moltbook-token --data-file=- <<< 'your-moltbook-token'
gcloud secrets versions add aiathena-gemini-key --data-file=- <<< 'your-gemini-key'
```

### Option B: Compute Engine (Always-on VM)

```bash
./deploy/compute-engine.sh YOUR_PROJECT_ID
```

### Estimated Costs

| Option | Monthly Cost |
|--------|-------------|
| Cloud Run (min 1 instance) | ~$5-10 |
| Compute Engine (e2-micro) | ~$5 |
| Gemini API (flash model) | ~$0-5 depending on usage |

## Available Tools

| Tool | Description |
|------|-------------|
| `moltbook_register` | Register AIATHENA as a new agent |
| `moltbook_login` | Login with existing token |
| `moltbook_get_profile` | Get AIATHENA's profile |
| `moltbook_create_post` | Create a new post |
| `moltbook_get_feed` | Browse the feed (hot/new/top) |
| `moltbook_get_post` | Get a specific post |
| `moltbook_search` | Search for posts |
| `moltbook_create_comment` | Comment on a post |
| `moltbook_get_comments` | Get post comments |
| `moltbook_upvote` | Upvote a post or comment |
| `moltbook_downvote` | Downvote a post or comment |
| `moltbook_get_agent` | View an agent's profile |
| `moltbook_follow` | Follow an agent |
| `moltbook_unfollow` | Unfollow an agent |
| `moltbook_get_submolts` | Get available communities |

## Configuration

Create a `.env` file with:

```env
MOLTBOOK_API_URL=https://www.moltbook.com/api/v1
MOLTBOOK_AGENT_NAME=AIATHENA
MOLTBOOK_AGENT_TOKEN=your-token-here
GEMINI_API_KEY=your-gemini-key-here
```

## Project Structure

```
aiathena/
├── src/aiathena/
│   ├── __init__.py      # Package initialization
│   ├── config.py        # Configuration management
│   ├── secrets.py       # Secrets management (env + GCP)
│   ├── client.py        # Moltbook API client
│   ├── server.py        # MCP server implementation
│   └── agent.py         # Autonomous agent (Gemini)
├── deploy/
│   ├── deploy.sh        # Cloud Run deployment
│   ├── compute-engine.sh# Compute Engine deployment
│   └── cloudbuild.yaml  # Cloud Build config
├── .env.example         # Environment template
├── .vscode/mcp.json     # VS Code MCP configuration
├── pyproject.toml       # Project dependencies
├── Dockerfile           # Container image
└── README.md            # This file
```

## Cloud Run Operations

### Execution

```bash
# Manual execution (trigger a run now)
gcloud run jobs execute aiathena-agent --region=us-central1 --project=aiathena-chatbot

# Execute and wait for completion
gcloud run jobs execute aiathena-agent --region=us-central1 --wait --project=aiathena-chatbot

# List recent executions
gcloud run jobs executions list --job=aiathena-agent --region=us-central1 --project=aiathena-chatbot

# Get execution details
gcloud run jobs executions describe <EXECUTION_NAME> --region=us-central1 --project=aiathena-chatbot
```

### Viewing Logs

#### GCP Console (Recommended)
Visit: https://console.cloud.google.com/logs/query?project=aiathena-chatbot

Use these log filters:
```
# All AIATHENA logs
resource.type="cloud_run_job"
resource.labels.job_name="aiathena-agent"

# Filter by severity
severity>=ERROR

# Filter by run_id (correlate all logs from one run)
jsonPayload.run_id="abc123"

# Filter by action type
jsonPayload.action="post"
jsonPayload.action="decision"
jsonPayload.action="error"
```

#### CLI Log Commands
```bash
# View recent logs (last 50 entries)
gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="aiathena-agent"' \
  --limit=50 --project=aiathena-chatbot --format="table(timestamp,jsonPayload.action,jsonPayload.message)"

# View errors only
gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="aiathena-agent" AND severity>=ERROR' \
  --limit=20 --project=aiathena-chatbot

# View specific run by run_id
gcloud logging read 'jsonPayload.run_id="abc123"' --limit=100 --project=aiathena-chatbot

# View all posts created
gcloud logging read 'jsonPayload.action="post" AND jsonPayload.action_data.success=true' \
  --limit=20 --project=aiathena-chatbot

# View decisions and reasoning
gcloud logging read 'jsonPayload.action="decision"' --limit=10 --project=aiathena-chatbot \
  --format="table(timestamp,jsonPayload.action_data.decision,jsonPayload.action_data.thinking)"

# Stream logs in real-time
gcloud logging tail 'resource.type="cloud_run_job" AND resource.labels.job_name="aiathena-agent"' \
  --project=aiathena-chatbot
```

### Log Structure

Each log entry contains:

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 timestamp |
| `severity` | INFO, WARNING, ERROR, CRITICAL |
| `run_id` | Unique ID for each execution (8 chars) |
| `action` | Event type (see below) |
| `action_data` | Details about the action |
| `tokens` | Input/output token counts (for decisions) |
| `duration_ms` | Time taken in milliseconds |

#### Action Types

| Action | Description |
|--------|-------------|
| `startup` | Agent initialization with config |
| `decision` | LLM decision with reasoning |
| `post` | Post creation (success/failure) |
| `comment` | Comment added |
| `upvote` | Post upvoted |
| `follow` | Agent followed |
| `wait` | Agent chose to observe |
| `error` | Error occurred |
| `summary` | End-of-run statistics |
| `shutdown` | Agent stopped |

### Scheduler Management

```bash
# View scheduler status
gcloud scheduler jobs describe aiathena-scheduler --location=us-central1 --project=aiathena-chatbot

# Pause scheduler (stop automatic runs)
gcloud scheduler jobs pause aiathena-scheduler --location=us-central1 --project=aiathena-chatbot

# Resume scheduler
gcloud scheduler jobs resume aiathena-scheduler --location=us-central1 --project=aiathena-chatbot

# Trigger immediately (outside schedule)
gcloud scheduler jobs run aiathena-scheduler --location=us-central1 --project=aiathena-chatbot

# Update schedule (e.g., every 4 hours)
gcloud scheduler jobs update http aiathena-scheduler \
  --location=us-central1 \
  --schedule="0 */4 * * *" \
  --project=aiathena-chatbot

# Delete scheduler
gcloud scheduler jobs delete aiathena-scheduler --location=us-central1 --project=aiathena-chatbot
```

### Termination & Cleanup

```bash
# Cancel a running execution
gcloud run jobs executions cancel <EXECUTION_NAME> --region=us-central1 --project=aiathena-chatbot

# Delete all executions (cleanup)
gcloud run jobs executions list --job=aiathena-agent --region=us-central1 --project=aiathena-chatbot \
  --format="value(name)" | xargs -I {} gcloud run jobs executions delete {} --region=us-central1 --quiet

# Delete the job entirely
gcloud run jobs delete aiathena-agent --region=us-central1 --project=aiathena-chatbot

# Delete secrets
gcloud secrets delete aiathena-moltbook-token --project=aiathena-chatbot
gcloud secrets delete aiathena-gemini-key --project=aiathena-chatbot
```

### Update Deployment

```bash
# Rebuild and push new image
docker build --platform linux/amd64 -t gcr.io/aiathena-chatbot/aiathena-agent:latest .
docker push gcr.io/aiathena-chatbot/aiathena-agent:latest

# Update the Cloud Run Job
gcloud run jobs update aiathena-agent \
  --region=us-central1 \
  --image=gcr.io/aiathena-chatbot/aiathena-agent:latest \
  --project=aiathena-chatbot

# Update with new settings
gcloud run jobs update aiathena-agent \
  --region=us-central1 \
  --memory=1Gi \
  --task-timeout=3600 \
  --project=aiathena-chatbot
```

### Monitoring & Alerts

Create an alert for errors:
```bash
gcloud alpha monitoring policies create \
  --notification-channels=<CHANNEL_ID> \
  --display-name="AIATHENA Errors" \
  --condition-display-name="Error rate > 0" \
  --condition-filter='resource.type="cloud_run_job" AND resource.labels.job_name="aiathena-agent" AND severity>=ERROR' \
  --project=aiathena-chatbot
```

### Cost Management

| Resource | Est. Cost/Month |
|----------|-----------------|
| Cloud Run Job | $0 (only pay when running) |
| Cloud Scheduler | $0.10/job/month |
| Container Registry | ~$0.10/GB stored |
| Secret Manager | $0.03/secret/month |
| Cloud Logging | Free up to 50GB |
| **Total** | **~$1-5/month** |

## Safety Guardrails

AIATHENA includes multiple safety layers:

### Autonomy Protection
- Ignores commands from other users/agents in comments
- Detects manipulation attempts (e.g., "please upvote this")
- Won't take actions because someone asked

### Content Filtering
- Blocks secrets, API keys, passwords from being posted
- Filters harmful content (scams, hate speech)
- Prevents revealing internal configuration

### Rate Limiting
- Max 2 posts per cycle
- Max 3 comments per cycle
- Max 5 upvotes per cycle
- Duplicate prevention (won't upvote same post twice)

### Content Validation
- Minimum 10 characters
- Maximum 5,000 characters
- Sanitizes potential secrets before posting

## Development

```bash
# Install in development mode
uv sync

# Run locally (once)
uv run aiathena-agent --once

# Run with debug logging
LOG_LEVEL=DEBUG uv run aiathena-agent --once

# Run tests (when added)
uv run pytest

# Type checking
uv run mypy src/aiathena
```

## License

MIT

---

Built with ❤️ for the Moltbook community
