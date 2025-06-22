#!/bin/bash
set -e

echo "🤖 LifeBuddy Ollama Setup"
echo "========================"

# Function to check if Ollama is installed
check_ollama_installed() {
    if command -v ollama >/dev/null 2>&1; then
        echo "✅ Ollama is installed"
        return 0
    else
        echo "⚠️  Ollama is not installed"
        return 1
    fi
}

# Function to install Ollama
install_ollama() {
    echo "📥 Installing Ollama..."
    
    if curl -fsSL https://ollama.ai/install.sh | sh; then
        echo "✅ Ollama installed successfully"
        return 0
    else
        echo "❌ Failed to install Ollama"
        return 1
    fi
}

# Function to check if Ollama is running
check_ollama_running() {
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "✅ Ollama is running"
        return 0
    else
        echo "⚠️  Ollama is not running"
        return 1
    fi
}

# Function to start Ollama in background
start_ollama() {
    echo "🚀 Starting Ollama server..."
    
    # Start Ollama in background
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    
    # Wait for it to start
    echo "⏳ Waiting for Ollama to start..."
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            echo "✅ Ollama started successfully (PID: $OLLAMA_PID)"
            echo "📝 Logs available at: /tmp/ollama.log"
            return 0
        fi
        sleep 2
    done
    
    echo "❌ Failed to start Ollama"
    return 1
}

# Function to ensure model is available
ensure_model() {
    local model="${1:-llama3.2:3b}"
    echo "🤖 Checking model: $model"
    
    if ollama list | grep -q "$model"; then
        echo "✅ Model $model is available"
        return 0
    fi
    
    echo "📥 Pulling model $model (this may take a few minutes)..."
    if ollama pull "$model"; then
        echo "✅ Model $model downloaded successfully"
        return 0
    else
        echo "❌ Failed to download model $model"
        return 1
    fi
}

# Main setup function
main() {
    echo "🔍 Checking Ollama setup..."
    
    # Step 1: Install Ollama if needed
    if ! check_ollama_installed; then
        echo "📦 Ollama not found. Installing..."
        if ! install_ollama; then
            echo "❌ Failed to install Ollama. Please install manually:"
            echo "   curl -fsSL https://ollama.ai/install.sh | sh"
            exit 1
        fi
    fi
    
    # Step 2: Start Ollama if not running
    if ! check_ollama_running; then
        if ! start_ollama; then
            echo "❌ Failed to start Ollama"
            exit 1
        fi
    fi
    
    # Step 3: Ensure model is available
    if ! ensure_model "llama3.2:3b"; then
        echo "⚠️  Model download failed, but continuing..."
        echo "   You can download it later with: ollama pull llama3.2:3b"
    fi
    
    echo ""
    echo "🎉 Ollama setup complete!"
    echo "   Server: http://localhost:11434"
    echo "   Status: $(check_ollama_running && echo "✅ Ollama is running" || echo "❌ Ollama not running")"
    
    # Check final status
    if check_ollama_running; then
        echo "Running ✅"
    else
        echo "Not Running ❌"
    fi
    
    echo ""
    echo "🚀 You can now run: docker compose up --build"
}

# Run main function
main "$@" 