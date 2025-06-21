#!/bin/bash

# LifeBuddy Docker Entrypoint Script
# Handles Apple Health data processing, Ollama setup, and service startup

set -e

echo "🌟 Starting LifeBuddy Docker Container"
echo "=" * 50

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if Ollama is running
check_ollama() {
    curl -s http://localhost:11434/api/tags >/dev/null 2>&1
}

# Function to start Ollama in background
start_ollama() {
    log "🚀 Starting Ollama server..."
    ollama serve &
    OLLAMA_PID=$!
    
    # Wait for Ollama to start
    for i in {1..30}; do
        if check_ollama; then
            log "✅ Ollama server started successfully"
            return 0
        fi
        log "⏳ Waiting for Ollama server... ($i/30)"
        sleep 2
    done
    
    log "❌ Failed to start Ollama server"
    return 1
}

# Function to setup Ollama model
setup_ollama_model() {
    log "📥 Setting up Ollama model: $OLLAMA_MODEL"
    
    # Check if model exists
    if ollama list | grep -q "$OLLAMA_MODEL"; then
        log "✅ Model $OLLAMA_MODEL already exists"
        return 0
    fi
    
    # Pull the model
    log "📥 Downloading model $OLLAMA_MODEL (this may take a few minutes)..."
    if ollama pull "$OLLAMA_MODEL"; then
        log "✅ Model $OLLAMA_MODEL downloaded successfully"
        return 0
    else
        log "❌ Failed to download model $OLLAMA_MODEL"
        return 1
    fi
}

# Function to check for Apple Health data in Downloads
check_downloads_for_export() {
    log "🔍 Checking for Apple Health export in Downloads folder..."
    
    # Common paths for Downloads folder (mounted from host)
    DOWNLOAD_PATHS=(
        "/host/Downloads"
        "/downloads"
        "/mnt/downloads"
    )
    
    for download_path in "${DOWNLOAD_PATHS[@]}"; do
        if [ -d "$download_path" ]; then
            log "📁 Found Downloads folder: $download_path"
            
            # Look for export.zip or apple_health_export files
            export_files=$(find "$download_path" -name "*export*.zip" -o -name "*apple*health*.zip" -o -name "*Export*.zip" 2>/dev/null | head -5)
            
            if [ -n "$export_files" ]; then
                log "📦 Found potential Apple Health export files:"
                echo "$export_files" | while read -r file; do
                    log "   - $(basename "$file")"
                done
                
                # Copy the most recent export file
                latest_export=$(echo "$export_files" | head -1)
                log "📋 Copying latest export: $(basename "$latest_export")"
                
                cp "$latest_export" "/app/data/raw/apple_health_export/"
                log "✅ Copied Apple Health export to container"
                return 0
            fi
        fi
    done
    
    log "ℹ️  No Apple Health export found in Downloads folder"
    return 1
}

# Function to check for existing Apple Health data
check_existing_data() {
    log "🔍 Checking for existing Apple Health data..."
    
    # Check if export files exist
    if ls /app/data/raw/apple_health_export/*.zip >/dev/null 2>&1; then
        log "📦 Found Apple Health export files"
        return 0
    fi
    
    # Check if database already exists
    if [ -f "$DATABASE_PATH" ]; then
        log "🗄️  Found existing database: $DATABASE_PATH"
        
        # Quick check if database has data
        record_count=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM health_records;" 2>/dev/null || echo "0")
        if [ "$record_count" -gt 0 ]; then
            log "✅ Database contains $record_count health records"
            return 0
        else
            log "⚠️  Database exists but appears empty"
        fi
    fi
    
    return 1
}

# Function to process Apple Health data
process_health_data() {
    log "🏥 Processing Apple Health data..."
    
    export_files=$(ls /app/data/raw/apple_health_export/*.zip 2>/dev/null || echo "")
    
    if [ -n "$export_files" ]; then
        # Process the first export file found
        export_file=$(echo "$export_files" | head -1)
        log "📊 Processing: $(basename "$export_file")"
        
        if python app/ingestion/apple_health.py "$export_file"; then
            log "✅ Apple Health data processed successfully"
            
            # Show database stats
            if [ -f "$DATABASE_PATH" ]; then
                record_count=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM health_records;" 2>/dev/null || echo "0")
                workout_count=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM workouts;" 2>/dev/null || echo "0")
                log "📈 Database created with $record_count health records and $workout_count workouts"
            fi
            return 0
        else
            log "❌ Failed to process Apple Health data"
            return 1
        fi
    else
        log "⚠️  No Apple Health export files found to process"
        return 1
    fi
}

# Function to start FastAPI
start_fastapi() {
    log "🚀 Starting FastAPI backend..."
    python -m app.api.main &
    FASTAPI_PID=$!
    
    # Wait for FastAPI to start
    for i in {1..20}; do
        if curl -s http://localhost:8000/health/status >/dev/null 2>&1; then
            log "✅ FastAPI backend started successfully"
            return 0
        fi
        log "⏳ Waiting for FastAPI backend... ($i/20)"
        sleep 2
    done
    
    log "❌ Failed to start FastAPI backend"
    return 1
}

# Function to start Streamlit
start_streamlit() {
    log "🎨 Starting Streamlit frontend..."
    streamlit run app/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
    STREAMLIT_PID=$!
    
    # Wait for Streamlit to start
    for i in {1..20}; do
        if curl -s http://localhost:8501 >/dev/null 2>&1; then
            log "✅ Streamlit frontend started successfully"
            return 0
        fi
        log "⏳ Waiting for Streamlit frontend... ($i/20)"
        sleep 2
    done
    
    log "❌ Failed to start Streamlit frontend"
    return 1
}

# Function to cleanup on exit
cleanup() {
    log "🔄 Shutting down LifeBuddy services..."
    
    if [ -n "$STREAMLIT_PID" ]; then
        kill $STREAMLIT_PID 2>/dev/null || true
    fi
    
    if [ -n "$FASTAPI_PID" ]; then
        kill $FASTAPI_PID 2>/dev/null || true
    fi
    
    if [ -n "$OLLAMA_PID" ]; then
        kill $OLLAMA_PID 2>/dev/null || true
    fi
    
    log "👋 LifeBuddy container stopped"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Main execution flow
main() {
    log "🌟 LifeBuddy Health Companion Starting..."
    
    # Step 1: Start Ollama
    if start_ollama; then
        setup_ollama_model
    else
        log "⚠️  Continuing without Ollama (you can use other providers)"
    fi
    
    # Step 2: Check for Apple Health data
    data_processed=false
    
    # First check Downloads folder
    if check_downloads_for_export; then
        if process_health_data; then
            data_processed=true
        fi
    fi
    
    # If no new data, check for existing data
    if [ "$data_processed" = false ]; then
        if check_existing_data; then
            log "✅ Using existing health data"
            data_processed=true
        fi
    fi
    
    # Show data status
    if [ "$data_processed" = true ]; then
        log "🎉 Health data is ready for analysis!"
    else
        log "ℹ️  No health data found - you can still use the chat interface"
        log "💡 To add data: copy your Apple Health export.zip to the data/raw/apple_health_export folder"
    fi
    
    # Step 3: Start services
    if start_fastapi && start_streamlit; then
        log "🎉 LifeBuddy is ready!"
        log "📱 Access the interface at: http://localhost:8501"
        log "🔗 API documentation at: http://localhost:8000/docs"
        
        # Keep container running
        log "🔄 Services running... (Ctrl+C to stop)"
        wait
    else
        log "❌ Failed to start LifeBuddy services"
        exit 1
    fi
}

# Run main function
main "$@" 