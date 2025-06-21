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

# Function to create systemd service (Linux) or launchd service (macOS)
create_auto_start_service() {
    echo "🔧 Setting up Ollama auto-start..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - create launchd plist
        PLIST_PATH="$HOME/Library/LaunchAgents/com.ollama.server.plist"
        
        cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which ollama)</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/.ollama/logs/server.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/.ollama/logs/server.error.log</string>
</dict>
</plist>
EOF
        
        # Create log directory
        mkdir -p "$HOME/.ollama/logs"
        
        # Load the service
        launchctl load "$PLIST_PATH" 2>/dev/null || true
        
        echo "✅ Ollama auto-start service created (macOS)"
        echo "   Ollama will start automatically on login"
        
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux - create systemd user service
        SERVICE_PATH="$HOME/.config/systemd/user/ollama.service"
        mkdir -p "$(dirname "$SERVICE_PATH")"
        
        cat > "$SERVICE_PATH" << EOF
[Unit]
Description=Ollama Server
After=network.target

[Service]
Type=simple
ExecStart=$(which ollama) serve
Restart=always
RestartSec=3
Environment=HOME=$HOME

[Install]
WantedBy=default.target
EOF
        
        # Reload systemd and enable service
        systemctl --user daemon-reload
        systemctl --user enable ollama.service
        systemctl --user start ollama.service
        
        echo "✅ Ollama auto-start service created (Linux)"
        echo "   Ollama will start automatically on login"
    else
        echo "⚠️  Auto-start service not supported on this OS"
        echo "   You'll need to run 'ollama serve' manually"
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
    
    # Step 4: Offer to set up auto-start
    echo ""
    read -p "🤖 Would you like Ollama to start automatically on login? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_auto_start_service
    else
        echo "ℹ️  Skipping auto-start setup"
        echo "   Remember to run 'ollama serve' before using LifeBuddy"
    fi
    
    echo ""
    echo "🎉 Ollama setup complete!"
    echo "   Server: http://localhost:11434"
    echo "   Status: $(check_ollama_running && echo "Running ✅" || echo "Stopped ❌")"
    echo ""
    echo "🚀 You can now run: docker compose up --build"
}

# Run main function
main "$@" 