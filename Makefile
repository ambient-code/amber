.PHONY: help install dev test lint format clean docker-build docker-push k8s-deploy k8s-delete

help:
	@echo "Amber LangGraph - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install production dependencies"
	@echo "  make dev           Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test          Run test suite"
	@echo "  make lint          Run linters"
	@echo "  make format        Format code"
	@echo "  make run           Run service locally"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  Build container image"
	@echo "  make docker-push   Push image to registry"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-deploy    Deploy to Kubernetes"
	@echo "  make k8s-delete    Delete from Kubernetes"
	@echo "  make k8s-logs      View logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove build artifacts"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=amber --cov-report=html

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

run:
	python -m amber.service

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:
	docker build -t amber-langgraph:latest .
	docker tag amber-langgraph:latest quay.io/ambient_code/amber-langgraph:latest

docker-push:
	docker push quay.io/ambient_code/amber-langgraph:latest

k8s-deploy:
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/cronjobs.yaml

k8s-delete:
	kubectl delete -f k8s/cronjobs.yaml
	kubectl delete -f k8s/deployment.yaml

k8s-logs:
	kubectl logs -n ambient-code -l app=amber-langgraph --tail=100 -f

k8s-status:
	kubectl get pods -n ambient-code -l app=amber-langgraph
	kubectl get svc -n ambient-code amber-langgraph
	kubectl get cronjobs -n ambient-code -l app=amber-langgraph
