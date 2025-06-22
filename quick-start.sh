#!/bin/bash

# LifeBuddy Quick Start Script
# Simple universal timezone setup using UTC offsets

set -e

echo "🚀 Starting LifeBuddy..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the LifeBuddy root directory"
    exit 1
fi

# Check if TZ is already set
if [ -z "$TZ" ]; then
    echo ""
    echo "🌍 Please set your timezone as UTC offset:"
    echo "   Examples:"
    echo "   • UTC-8 (Pacific Time)"
    echo "   • UTC-5 (Eastern Time)" 
    echo "   • UTC+0 (London/GMT)"
    echo "   • UTC+1 (Berlin/Paris)"
    echo "   • UTC+5:30 (India)"
    echo "   • UTC+9 (Japan/Korea)"
    echo ""
    echo "💡 Usage: TZ=UTC-8 ./quick-start.sh"
    echo "💡 Or set permanently: export TZ=UTC-8"
    echo ""
    exit 1
fi

echo "🌍 Using timezone: $TZ"

# Setup Ollama
echo "📦 Setting up Ollama..."
if [ -f "deployment/setup-ollama.sh" ]; then
    chmod +x deployment/setup-ollama.sh
    ./deployment/setup-ollama.sh
else
    echo "❌ Error: deployment/setup-ollama.sh not found"
    exit 1
fi

# Start Docker containers
echo "🐳 Starting LifeBuddy containers..."
cd deployment
docker compose up --build

echo "🎉 LifeBuddy should now be running!"
echo "   • Streamlit UI: http://localhost:8501"
echo "   • FastAPI docs: http://localhost:8000/docs" 