# Quick Start Guide

Get Amber LangGraph running in 5 minutes.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- API keys: Anthropic, GitHub

## Installation

```bash
cd amber-langgraph

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install
pip install -e .
```

## Configuration

```bash
cp .env.example .env
```

Edit `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
POSTGRES_URL=postgresql://user:pass@localhost:5432/amber
```

## Run Locally

```bash
python -m amber.service
```

Service starts on http://localhost:8000

## Test Endpoints

Health check:
```bash
curl http://localhost:8000/health
```

On-demand query:
```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "on-demand",
    "trigger": {"query": "What are the main components of ACP?"},
    "session_id": "demo-123",
    "project_name": "platform",
    "repositories": ["https://github.com/ambient-code/platform"]
  }'
```

## Deploy to Kubernetes

```bash
# Create secrets
kubectl create secret generic anthropic-api-key \
  --from-literal=api-key=$ANTHROPIC_API_KEY \
  -n ambient-code

kubectl create secret generic github-token \
  --from-literal=token=$GITHUB_TOKEN \
  -n ambient-code

kubectl create secret generic postgres-credentials \
  --from-literal=connection-string=$POSTGRES_URL \
  -n ambient-code

# Deploy
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/cronjobs.yaml

# Check status
kubectl get pods -n ambient-code -l app=amber-langgraph
kubectl logs -n ambient-code -l app=amber-langgraph
```

## Verify Deployment

```bash
# Port forward
kubectl port-forward -n ambient-code svc/amber-langgraph 8000:8000

# Test health
curl http://localhost:8000/health
```

## Common Issues

**PostgreSQL connection failed:**
- Check POSTGRES_URL format
- Verify database exists
- Check network connectivity

**API key invalid:**
- Verify ANTHROPIC_API_KEY is correct
- Check key has sufficient quota

**Pod won't start:**
- Check logs: `kubectl logs -n ambient-code <pod-name>`
- Verify secrets exist: `kubectl get secrets -n ambient-code`
- Check RBAC: `kubectl auth can-i create agenticsessions --as=system:serviceaccount:ambient-code:amber-langgraph -n ambient-code`

## Next Steps

- Read [README.md](README.md) for full documentation
- See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for architecture details
- Review [AMBER_LANGGRAPH_ARCHITECTURE.md](../AMBER_LANGGRAPH_ARCHITECTURE.md) for design rationale
