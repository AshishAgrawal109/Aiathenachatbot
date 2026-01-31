#!/bin/bash
# Deploy AIATHENA Agent to Google Compute Engine (alternative to Cloud Run)
# Use this if you need a persistent VM instead of serverless
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated
#   2. A GCP project with billing enabled
#
# Usage:
#   ./deploy/compute-engine.sh [PROJECT_ID] [ZONE]

set -e

# Configuration
PROJECT_ID="${1:-$(gcloud config get-value project)}"
ZONE="${2:-us-central1-a}"
INSTANCE_NAME="aiathena-agent"
MACHINE_TYPE="e2-micro"  # Cheapest option, ~$5/month

echo "🦉 Deploying AIATHENA Agent to Compute Engine"
echo "   Project: ${PROJECT_ID}"
echo "   Zone: ${ZONE}"
echo "   Machine type: ${MACHINE_TYPE}"
echo ""

# Check if gcloud is authenticated
if ! gcloud auth print-identity-token &> /dev/null; then
    echo "❌ Not authenticated with gcloud. Run: gcloud auth login"
    exit 1
fi

# Enable required APIs
echo "📦 Enabling required APIs..."
gcloud services enable compute.googleapis.com --project="${PROJECT_ID}"

# Create startup script
STARTUP_SCRIPT=$(cat << 'EOF'
#!/bin/bash
set -e

# Install dependencies
apt-get update
apt-get install -y python3-pip python3-venv git

# Create aiathena user
useradd -m -s /bin/bash aiathena || true

# Clone/update repository (you'll need to customize this)
cd /home/aiathena
if [ ! -d "aiathena" ]; then
    git clone https://github.com/YOUR_USERNAME/aiathena.git
else
    cd aiathena && git pull
fi

cd /home/aiathena/aiathena

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install uv and dependencies
pip install uv
uv pip install -e .

# Get secrets from metadata
MOLTBOOK_TOKEN=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/moltbook-token" -H "Metadata-Flavor: Google")
GEMINI_KEY=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/gemini-api-key" -H "Metadata-Flavor: Google")

# Create env file
cat > .env << ENVFILE
MOLTBOOK_API_URL=https://www.moltbook.com/api/v1
MOLTBOOK_AGENT_NAME=AIATHENA
MOLTBOOK_AGENT_TOKEN=${MOLTBOOK_TOKEN}
GEMINI_API_KEY=${GEMINI_KEY}
GEMINI_MODEL=gemini-2.0-flash
ENVFILE

chown -R aiathena:aiathena /home/aiathena

# Create systemd service
cat > /etc/systemd/system/aiathena.service << SERVICE
[Unit]
Description=AIATHENA Moltbook Agent
After=network.target

[Service]
Type=simple
User=aiathena
WorkingDirectory=/home/aiathena/aiathena
Environment=PATH=/home/aiathena/aiathena/.venv/bin
ExecStart=/home/aiathena/aiathena/.venv/bin/python -m aiathena.agent --interval 120
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
SERVICE

# Start service
systemctl daemon-reload
systemctl enable aiathena
systemctl start aiathena

echo "AIATHENA agent started!"
EOF
)

# Check if instance exists
if gcloud compute instances describe "${INSTANCE_NAME}" --zone="${ZONE}" --project="${PROJECT_ID}" &> /dev/null; then
    echo "⚠️  Instance already exists. Deleting and recreating..."
    gcloud compute instances delete "${INSTANCE_NAME}" \
        --zone="${ZONE}" \
        --project="${PROJECT_ID}" \
        --quiet
fi

# Create the instance
echo ""
echo "🔨 Creating Compute Engine instance..."
gcloud compute instances create "${INSTANCE_NAME}" \
    --zone="${ZONE}" \
    --machine-type="${MACHINE_TYPE}" \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size=10GB \
    --metadata="moltbook-token=YOUR_MOLTBOOK_TOKEN,gemini-api-key=YOUR_GEMINI_API_KEY" \
    --metadata-from-file="startup-script=<(echo '${STARTUP_SCRIPT}')" \
    --scopes=cloud-platform \
    --project="${PROJECT_ID}"

echo ""
echo "✅ Instance created!"
echo ""
echo "📋 Next steps:"
echo "   1. Update the instance metadata with your actual tokens:"
echo "      gcloud compute instances add-metadata ${INSTANCE_NAME} \\"
echo "          --zone=${ZONE} \\"
echo "          --metadata=moltbook-token=YOUR_TOKEN,gemini-api-key=YOUR_KEY"
echo ""
echo "   2. SSH into the instance:"
echo "      gcloud compute ssh ${INSTANCE_NAME} --zone=${ZONE} --project=${PROJECT_ID}"
echo ""
echo "   3. Check agent logs:"
echo "      sudo journalctl -u aiathena -f"
echo ""
echo "   4. Restart the agent:"
echo "      sudo systemctl restart aiathena"
