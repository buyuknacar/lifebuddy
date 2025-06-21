# 🐳 LifeBuddy Docker Setup

Run LifeBuddy as a complete containerized solution with Ollama, FastAPI, and Streamlit.

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Build and start the container
docker-compose up --build

# Or run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Option 2: Direct Docker Commands

```bash
# Build the image
docker build -t lifebuddy .

# Run the container
docker run -d \
  --name lifebuddy-app \
  -p 8000:8000 \
  -p 8501:8501 \
  -v ./data:/app/data \
  -v ~/Downloads:/host/Downloads:ro \
  lifebuddy

# View logs
docker logs -f lifebuddy-app

# Stop the container
docker stop lifebuddy-app
docker rm lifebuddy-app
```

## 📱 Access the Application

Once the container is running:

- **Streamlit UI**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health/status

## 📊 Apple Health Data Integration

### Automatic Detection

The container automatically looks for Apple Health exports in your Downloads folder:

1. Export your Apple Health data from the Health app
2. Save the export.zip file to your Downloads folder
3. Start the container - it will automatically detect and process the data

### Manual Setup

If automatic detection doesn't work:

1. Create the data directory: `mkdir -p data/raw/apple_health_export`
2. Copy your export.zip: `cp ~/Downloads/export.zip data/raw/apple_health_export/`
3. Restart the container: `docker-compose restart`

## 🔧 Configuration

### Environment Variables

The Docker container uses several environment variables for configuration:

- `LLM_PROVIDER=ollama` - Default AI provider (Ollama runs locally in container)
- `OLLAMA_BASE_URL=http://localhost:11434` - Ollama server URL
- `OLLAMA_MODEL=llama3.2:3b` - Default Ollama model
- `DATABASE_PATH=/app/data/lifebuddy.db` - SQLite database location

### Provider Selection

**Important**: The `LLM_PROVIDER=ollama` environment variable sets the **default** provider, but users can dynamically switch providers through the Streamlit interface:

- **Default (Ollama)**: Uses the local Ollama server running in the container
- **OpenAI/Anthropic/Google/Azure**: Requires API keys as environment variables

To use external providers, add their API keys to your `docker-compose.yml`:

```yaml
services:
  lifebuddy:
    # ... existing config ...
    environment:
      - OPENAI_API_KEY=your_openai_key_here
      - ANTHROPIC_API_KEY=your_anthropic_key_here
      - GOOGLE_API_KEY=your_google_key_here
      # etc.
```

The provider selection in the Streamlit UI will override the Docker default for each conversation.

### Resource Limits

Adjust CPU and memory limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 4G      # Maximum memory
      cpus: '2.0'     # Maximum CPU cores
```

## 📂 Data Persistence

The container mounts the following directories:

- `./data` → `/app/data` - Database and processed health data
- `~/Downloads` → `/host/Downloads` - Read-only access for auto-detection

Your health database persists between container restarts in the `./data` directory.

## 🔍 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Ollama Model Issues

```bash
# Access container shell
docker exec -it lifebuddy-app bash

# Check Ollama status
ollama list

# Manually pull model
ollama pull llama3.2:3b
```

### Health Data Not Processing

```bash
# Check if export file exists
ls -la data/raw/apple_health_export/

# Check processing logs
docker-compose logs | grep "Processing"

# Manually run processing
docker exec -it lifebuddy-app python app/ingestion/apple_health.py /app/data/raw/apple_health_export/export.zip
```

### Port Conflicts

If ports 8000 or 8501 are already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "8080:8000"   # Use port 8080 instead of 8000
  - "8502:8501"   # Use port 8502 instead of 8501
```

## 🔒 Security Notes

- Downloads folder is mounted read-only for security
- Container runs with minimal privileges
- No sensitive data is stored in the image
- All health data stays on your local machine

## 🛠️ Development

### Building for Development

```bash
# Build with development dependencies
docker build --target dev -t lifebuddy-dev .

# Run with code mounting for live reload
docker run -d \
  -p 8000:8000 -p 8501:8501 \
  -v ./app:/app/app \
  -v ./data:/app/data \
  lifebuddy-dev
```

### Custom Models

To use a different Ollama model:

```bash
# Set environment variable
export OLLAMA_MODEL=llama3.2:1b

# Or modify docker-compose.yml
environment:
  - OLLAMA_MODEL=llama3.2:1b
```

## 📋 System Requirements

- **Docker**: 20.10+
- **Memory**: 4GB+ recommended (for Ollama model)
- **Disk**: 2GB+ free space
- **OS**: Linux, macOS, Windows with WSL2

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Verify your export.zip file is valid
3. Ensure sufficient system resources
4. Try rebuilding: `docker-compose build --no-cache` 