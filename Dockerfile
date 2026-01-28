FROM python:3.11-slim

LABEL maintainer="jeremyeder@gmail.com"
LABEL description="Amber LangGraph AI Agent"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 amber && \
    mkdir -p /app && \
    chown -R amber:amber /app

WORKDIR /app

# Copy dependency files
COPY --chown=amber:amber pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy application code
COPY --chown=amber:amber src/ ./src/

# Switch to app user
USER amber

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run service
CMD ["python", "-m", "amber.service"]
