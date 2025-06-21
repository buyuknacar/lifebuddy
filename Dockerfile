# LifeBuddy Docker Container
# Lightweight container that connects to host Ollama
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LLM_PROVIDER=ollama
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV OLLAMA_MODEL=llama3.2:3b
ENV DATABASE_PATH=/app/data/lifebuddy.db

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry with pip retry configuration
RUN pip install --retries 5 --timeout 60 poetry

# Set pip configuration for better network handling
ENV PIP_RETRIES=5
ENV PIP_TIMEOUT=60
ENV PIP_DEFAULT_TIMEOUT=60

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Configure poetry and install dependencies (skip installing current project)
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-root

# Copy application code
COPY app/ ./app/
COPY docker-entrypoint.sh ./

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create data directories
RUN mkdir -p /app/data/raw/apple_health_export /app/logs

# Expose ports (removed Ollama port)
EXPOSE 8000 8501

# Health check (updated to not check Ollama)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/status || exit 1

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"] 