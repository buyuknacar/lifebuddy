"""
LifeBuddy main entry point.
Supports both FastAPI backend and Streamlit frontend modes.
"""
import sys
import argparse
import subprocess
import os
from pathlib import Path


def run_fastapi():
    """Run FastAPI backend server."""
    print("🚀 Starting LifeBuddy FastAPI backend...")
    try:
        import uvicorn
        uvicorn.run(
            "app.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError:
        print("❌ uvicorn not found. Install with: poetry install")
        sys.exit(1)


def run_streamlit():
    """Run Streamlit frontend."""
    print("🎨 Starting LifeBuddy Streamlit frontend...")
    
    # Get the path to the Streamlit app
    app_path = Path(__file__).parent / "ui" / "streamlit_app.py"
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Streamlit: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Streamlit not found. Install with: poetry install")
        sys.exit(1)


def run_both():
    """Run both FastAPI and Streamlit in parallel."""
    print("🚀 Starting both FastAPI backend and Streamlit frontend...")
    print("💡 Tip: Use Ctrl+C to stop both services")
    
    import threading
    import time
    
    # Start FastAPI in a thread
    def start_fastapi():
        try:
            import uvicorn
            uvicorn.run(
                "app.api.main:app",
                host="0.0.0.0",
                port=8000,
                log_level="info"
            )
        except Exception as e:
            print(f"❌ FastAPI error: {e}")
    
    # Start Streamlit in a thread
    def start_streamlit():
        time.sleep(2)  # Give FastAPI time to start
        app_path = Path(__file__).parent / "ui" / "streamlit_app.py"
        try:
            subprocess.run([
                sys.executable, "-m", "streamlit", "run", 
                str(app_path),
                "--server.port", "8501",
                "--server.address", "0.0.0.0"
            ])
        except Exception as e:
            print(f"❌ Streamlit error: {e}")
    
    # Start both services
    fastapi_thread = threading.Thread(target=start_fastapi, daemon=True)
    streamlit_thread = threading.Thread(target=start_streamlit, daemon=True)
    
    fastapi_thread.start()
    streamlit_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🔄 Shutting down LifeBuddy services...")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="LifeBuddy - AI Health Companion")
    parser.add_argument(
        "mode", 
        choices=["api", "ui", "both"], 
        nargs="?",
        default="both",
        help="Run mode: 'api' for FastAPI only, 'ui' for Streamlit only, 'both' for both (default)"
    )
    parser.add_argument(
        "--version", 
        action="version", 
        version="LifeBuddy 0.1.0"
    )
    
    args = parser.parse_args()
    
    print("🌟 LifeBuddy - Your AI Health Companion")
    print("=" * 50)
    
    # Check if health database exists
    db_path = os.getenv("DATABASE_PATH", "data/lifebuddy.db")
    if not os.path.exists(db_path):
        print(f"⚠️  Health database not found: {db_path}")
        print("💡 Import your Apple Health data first:")
        print("    poetry run python app/ingestion/apple_health.py <path_to_export.zip>")
        print()
    
    # Run based on mode
    if args.mode == "api":
        run_fastapi()
    elif args.mode == "ui":
        run_streamlit()
    elif args.mode == "both":
        run_both()


if __name__ == "__main__":
    main() 