# Amber - Codebase Intelligence Agent

AI-powered codebase intelligence for the Ambient Code Platform. Amber operates in multiple modes for autonomous code maintenance, issue triage, and development assistance.

## Features

- **On-Demand Consultation**: Interactive Q&A about your codebase  
- **Background Agent**: Autonomous issue triage and PR creation
- **Scheduled Health Checks**: Nightly dependency scans, weekly sprint planning
- **Webhook Integration**: Reactive intelligence for GitHub events
- **Constitution Compliance**: Automatic enforcement of project standards

## Quick Start

### Prerequisites

- Python 3.11-3.13 (not 3.14 yet)
- Anthropic API key
- GitHub token
- PostgreSQL 15+ (optional, for state persistence)

### Installation

```bash
git clone https://github.com/ambient-code/amber.git
cd amber
python3.11 -m venv venv
source venv/bin/activate
pip install -e .
```

### Configuration

```bash
cp .env.example .env
# Edit .env: ANTHROPIC_API_KEY, GITHUB_TOKEN, POSTGRES_URL (optional)
```

### Run

```bash
python -m amber.service
# Health check: curl http://localhost:8000/health
```

## Usage Examples

**On-Demand Query:**
```bash
curl -X POST http://localhost:8000/invoke -H "Content-Type: application/json" -d '{
  "mode": "on-demand",
  "trigger": {"query": "What changed this week?"},
  "session_id": "user-123",
  "project_name": "myproject",
  "repositories": ["https://github.com/owner/repo"]
}'
```

**Background Mode:**
```bash
curl -X POST http://localhost:8000/invoke-async -H "Content-Type: application/json" -d '{
  "mode": "background",
  "trigger": {"autonomous": true},
  "session_id": "bg-123",
  "project_name": "myproject",
  "repositories": ["https://github.com/owner/repo"]
}'
```

## Web UI (Optional)

Chat interface available in [amber-ui](../amber-ui/):
```bash
cd ../amber-ui && npm install && npm run dev
# Access: http://localhost:5003
```

## Deployment

**Docker:**
```bash
docker build -t amber:latest .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=... -e GITHUB_TOKEN=... amber:latest
```

**Kubernetes:**
```bash
kubectl create secret generic amber-secrets --from-literal=anthropic-api-key=... --from-literal=github-token=...
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/cronjobs.yaml
```

## Configuration

Key environment variables (see `.env.example` for all options):

| Variable | Required | Default |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | - |
| `GITHUB_TOKEN` | Yes | - |
| `POSTGRES_URL` | No | In-memory |
| `LLM_MODEL` | No | claude-sonnet-4-5 |
| `AUTO_MERGE_ENABLED` | No | false |

## Development

```bash
pip install -e ".[dev]"
pytest tests/        # Run tests
black src/ tests/    # Format
ruff check src/      # Lint
```

## License

MIT - See [LICENSE](LICENSE)
