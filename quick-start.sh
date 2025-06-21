#!/bin/bash

# LifeBuddy Quick Start Script
# This script handles the complete setup and startup process

set -e  # Exit on error

echo "🌟 LifeBuddy Quick Start"
echo "======================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the LifeBuddy root directory"
    exit 1
fi

# Step 1: Setup Ollama
echo "📦 Setting up Ollama..."
if [ -f "deployment/setup-ollama.sh" ]; then
    chmod +x deployment/setup-ollama.sh
    ./deployment/setup-ollama.sh
else
    echo "❌ Error: deployment/setup-ollama.sh not found"
    exit 1
fi

# Step 2: Start Docker containers
echo "🐳 Starting LifeBuddy containers..."
cd deployment
docker compose up --build

echo "🎉 LifeBuddy should now be running!"
echo "   • Streamlit UI: http://localhost:8501"
echo "   • FastAPI docs: http://localhost:8000/docs" 