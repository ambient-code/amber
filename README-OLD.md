# Amber LangGraph

Amber AI Agent reimplemented with LangGraph for the Ambient Code Platform.

## Overview

Amber is an intelligent codebase agent that operates in four modes:

- **On-demand:** Interactive consultation for Q&A and bug investigation
- **Background:** Autonomous issue triage and PR creation
- **Scheduled:** Periodic health checks (nightly, weekly, monthly)
- **Webhook:** Reactive intelligence for GitHub events

## Architecture

Built on LangGraph state machines with:

- Supervisor graph routing to specialized workflows
- Tool-augmented LLM agents using Claude Sonnet 4.5
- PostgreSQL checkpointing for long-running tasks
- FastAPI service with sync/async endpoints
- Kubernetes-native deployment

See [AMBER_LANGGRAPH_ARCHITECTURE.md](../AMBER_LANGGRAPH_ARCHITECTURE.md) for detailed design.

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (for checkpointing)
- Anthropic API key
- GitHub token

### Installation

```bash
# Clone repository
git clone https://github.com/ambient-code/amber-langgraph
cd amber-langgraph

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# For development
pip install -e ".[dev]"
```

### Configuration

Copy environment template:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `GITHUB_TOKEN`: GitHub personal access token
- `POSTGRES_URL`: PostgreSQL connection string

### Running Locally

```bash
# Start service
python -m amber.service

# Service runs on http://localhost:8000
# Health check: http://localhost:8000/health
```

### Docker

Build image:

```bash
docker build -t amber-langgraph:latest .
```

Run container:

```bash
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key \
  -e GITHUB_TOKEN=your-token \
  -e POSTGRES_URL=postgresql://... \
  amber-langgraph:latest
```

## Usage

### On-Demand Consultation

```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "on-demand",
    "trigger": {"query": "What changed in the backend this week?"},
    "session_id": "user-123",
    "project_name": "platform",
    "repositories": ["https://github.com/ambient-code/platform"]
  }'
```

### Background Agent (Async)

```bash
curl -X POST http://localhost:8000/invoke-async \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "background",
    "trigger": {"autonomous": true},
    "session_id": "bg-123",
    "project_name": "platform",
    "repositories": ["https://github.com/ambient-code/platform"]
  }'
```

### GitHub Webhook

Configure webhook in GitHub settings:

- Payload URL: `https://your-domain/webhook/issues.opened`
- Content type: `application/json`
- Events: Issues, Pull requests, Push

## Kubernetes Deployment

Deploy to Kubernetes:

```bash
# Create secrets
kubectl create secret generic anthropic-api-key \
  --from-literal=api-key=your-key \
  -n ambient-code

kubectl create secret generic github-token \
  --from-literal=token=your-token \
  -n ambient-code

kubectl create secret generic postgres-credentials \
  --from-literal=connection-string=postgresql://... \
  -n ambient-code

# Deploy service
kubectl apply -f k8s/deployment.yaml

# Deploy scheduled jobs
kubectl apply -f k8s/cronjobs.yaml
```

Check deployment:

```bash
kubectl get pods -n ambient-code -l app=amber-langgraph
kubectl logs -n ambient-code -l app=amber-langgraph
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Project Structure

```
amber-langgraph/
├── src/amber/
│   ├── models/          # State and data models
│   ├── tools/           # LangChain tools
│   ├── workflows/       # LangGraph workflows
│   ├── config.py        # Configuration
│   └── service.py       # FastAPI service
├── tests/               # Test suite
├── k8s/                 # Kubernetes manifests
├── docs/                # Documentation
├── Dockerfile           # Container image
└── pyproject.toml       # Dependencies
```

## Configuration

Key settings in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | Required |
| `GITHUB_TOKEN` | GitHub token | Required |
| `POSTGRES_URL` | PostgreSQL connection | Required |
| `LLM_MODEL` | Claude model | claude-sonnet-4-5-20250929 |
| `LLM_TEMPERATURE` | Temperature | 0.0 |
| `AUTO_MERGE_ENABLED` | Enable auto-merge | false |
| `AUTO_MERGE_MIN_CONFIDENCE` | Min confidence for merge | 0.95 |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

See [LICENSE](LICENSE) file.

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [ACP Constitution](../platform/.specify/memory/constitution.md)
- [Original Amber Definition](../platform/docs/agents/active/amber.md)
