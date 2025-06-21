#!/bin/bash

# LifeBuddy Docker Entrypoint Script
# Handles Apple Health data processing, Ollama setup, and service startup

set -e

echo "�� Starting LifeBuddy - AI Health Companion"
echo "============================================"

# Function to wait for host Ollama
wait_for_ollama() {
    echo "⏳ Waiting for Ollama on host (http://host.docker.internal:11434)..."
    
    for i in {1..30}; do
        if curl -s http://host.docker.internal:11434/api/tags > /dev/null 2>&1; then
            echo "✅ Ollama is available on host"
            return 0
        fi
        echo "   Attempt $i/30: Ollama not ready, waiting 2 seconds..."
        sleep 2
    done
    
    echo "⚠️  Ollama not found on host. Please ensure:"
    echo "   1. Ollama is installed on your host machine"
    echo "   2. Ollama is running: 'ollama serve'"
    echo "   3. Port 11434 is accessible"
    echo ""
    echo "   To install Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "   To start Ollama: ollama serve"
    echo ""
    echo "   Continuing without Ollama (you can use other providers)..."
    return 1
}

# Function to ensure Ollama model is available
ensure_ollama_model() {
    local model="$1"
    echo "🤖 Checking if model '$model' is available..."
    
    if curl -s http://host.docker.internal:11434/api/tags | grep -q "\"name\":\"$model\""; then
        echo "✅ Model '$model' is already available"
        return 0
    fi
    
    echo "📥 Model '$model' not found. Pulling it now..."
    echo "   This may take a few minutes on first run..."
    
    if curl -X POST http://host.docker.internal:11434/api/pull -d "{\"name\":\"$model\"}" 2>/dev/null; then
        echo "✅ Model '$model' pulled successfully"
        return 0
    else
        echo "⚠️  Failed to pull model '$model'. You can pull it manually:"
        echo "   ollama pull $model"
        return 1
    fi
}

# Function to check for Apple Health export
check_apple_health_export() {
    echo "🍎 Checking for Apple Health export..."
    
    if [ -f "/host/Downloads/export.xml" ]; then
        echo "✅ Found Apple Health export in Downloads"
        
        if [ ! -f "/app/data/lifebuddy.db" ] || [ "/host/Downloads/export.xml" -nt "/app/data/lifebuddy.db" ]; then
            echo "📊 Processing Apple Health data..."
            mkdir -p /app/data/raw/apple_health_export
            cp /host/Downloads/export.xml /app/data/raw/apple_health_export/
            
            # Process the data
            cd /app
            python -c "
from app.ingestion.apple_health import AppleHealthParser
parser = AppleHealthParser()
parser.parse_and_store('/app/data/raw/apple_health_export/export.xml')
print('✅ Apple Health data processed successfully')
" || echo "⚠️  Error processing Apple Health data"
        else
            echo "ℹ️  Apple Health data is up to date"
        fi
    else
        echo "ℹ️  No Apple Health export found in ~/Downloads"
        echo "   To add your data, export from iPhone Health app and save as ~/Downloads/export.xml"
    fi
}

# Main startup sequence
echo "🚀 Starting LifeBuddy services..."

# Check for Apple Health data first
check_apple_health_export

# Check if Ollama is available on host
if wait_for_ollama; then
    # Try to ensure the model is available
    ensure_ollama_model "${OLLAMA_MODEL:-llama3.2:3b}"
fi

# Start FastAPI backend
echo "🔧 Starting FastAPI backend..."
cd /app
python -m app.api.main &
FASTAPI_PID=$!

# Wait a moment for FastAPI to start
sleep 5

# Start Streamlit frontend
echo "🎨 Starting Streamlit frontend..."
streamlit run app/ui/streamlit_app.py --server.port=8501 --server.address=0.0.0.0 &
STREAMLIT_PID=$!

# Function to handle shutdown
cleanup() {
    echo "🛑 Shutting down LifeBuddy..."
    kill $FASTAPI_PID $STREAMLIT_PID 2>/dev/null || true
    wait
    echo "👋 LifeBuddy stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Wait for services and show status
sleep 10
echo ""
echo "🎉 LifeBuddy is ready!"
echo "   📱 Streamlit UI: http://localhost:8501"
echo "   🔧 FastAPI docs: http://localhost:8000/docs"
echo "   📊 Health status: http://localhost:8000/health/status"
echo ""

# Wait for processes
wait 