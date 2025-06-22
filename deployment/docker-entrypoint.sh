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
    
    local export_file=""
    local needs_unzip=false
    
    # Check for zip file first, then xml file
    if [ -f "/host/Downloads/export.zip" ]; then
        echo "✅ Found Apple Health export.zip in Downloads"
        export_file="/host/Downloads/export.zip"
        needs_unzip=true
    elif [ -f "/host/Downloads/export.xml" ]; then
        echo "✅ Found Apple Health export.xml in Downloads"
        export_file="/host/Downloads/export.xml"
        needs_unzip=false
    else
        echo "ℹ️  No Apple Health export found in ~/Downloads"
        echo "   To add your data, export from iPhone Health app and save as:"
        echo "   - ~/Downloads/export.zip (recommended - direct from Health app)"
        echo "   - ~/Downloads/export.xml (if manually extracted)"
        return 0
    fi
    
    echo "📊 Processing Apple Health data (full database overwrite)..."
    
    # Create directory for processing
    mkdir -p /app/data/raw/apple_health_export
    
    if [ "$needs_unzip" = true ]; then
        echo "📦 Unzipping export.zip..."
        cd /app/data/raw/apple_health_export
        
        # Copy and unzip the file
        cp "$export_file" ./export.zip
        
        # Check if unzip is available, install if needed
        if ! command -v unzip &> /dev/null; then
            echo "📥 Installing unzip utility..."
            apt-get update && apt-get install -y unzip
        fi
        
        # Unzip the file
        if unzip -o export.zip; then
            echo "✅ Successfully unzipped export.zip"
            # Find the export.xml file (it might be in a subdirectory)
            if [ -f "export.xml" ]; then
                echo "✅ Found export.xml in zip root"
            elif [ -f "apple_health_export/export.xml" ]; then
                echo "✅ Found export.xml in apple_health_export subdirectory"
                mv apple_health_export/export.xml ./
            else
                echo "⚠️  Could not find export.xml in the zip file"
                echo "   Zip contents:"
                ls -la
                return 1
            fi
        else
            echo "⚠️  Failed to unzip export.zip"
            return 1
        fi
        
        # Clean up zip file
        rm -f export.zip
    else
        # Copy XML file directly
        cp "$export_file" /app/data/raw/apple_health_export/export.xml
    fi
    
    # Verify we have the XML file
    if [ ! -f "/app/data/raw/apple_health_export/export.xml" ]; then
        echo "⚠️  export.xml not found after processing"
        return 1
    fi
    
    echo "🔄 Parsing and storing Apple Health data..."
    
    # Process the data (this will drop and recreate all tables)
    cd /app
    python -c "
from app.ingestion.apple_health import AppleHealthParser
parser = AppleHealthParser('/app/data/raw/apple_health_export/export.xml')
parser.create_database()
parser.parse_xml()
parser.save_to_database()
parser.print_summary()
print('✅ Apple Health data processed successfully (full overwrite)')
" || echo "⚠️  Error processing Apple Health data"
    
    # Optional: Remove the export file after processing to avoid reprocessing
    # rm "$export_file"
    echo "💡 Tip: Remove ~/Downloads/export.* to avoid reprocessing on next startup"
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