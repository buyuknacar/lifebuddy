# LifeBuddy Docker Container
# Includes Python environment, Ollama, and health data processing
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LLM_PROVIDER=ollama
ENV OLLAMA_BASE_URL=http://localhost:11434
ENV OLLAMA_MODEL=llama3.2:3b
ENV DATABASE_PATH=/app/data/lifebuddy.db

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    sqlite3 \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copy application code
COPY app/ ./app/
COPY setup_ollama.py ./
COPY docker-entrypoint.sh ./

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create data directories
RUN mkdir -p /app/data/raw/apple_health_export /app/logs

# Expose ports
EXPOSE 8000 8501 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/status || exit 1

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"] 