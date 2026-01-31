# AIATHENA Agent - Docker Image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv for fast package management
RUN pip install uv

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ src/

# Install dependencies (non-editable for production)
RUN uv pip install --system .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command: run agent once (Cloud Scheduler triggers every 2 hours)
CMD ["python", "-m", "aiathena.agent", "--once"]
