#!/usr/bin/env python3
"""
Simple Ollama setup script for LifeBuddy.
Run this to automatically install and configure Ollama.
"""

if __name__ == "__main__":
    try:
        from app.core.ollama_setup import OllamaSetup
        
        print("🤖 LifeBuddy - Automatic Ollama Setup")
        print("=" * 40)
        
        setup = OllamaSetup()
        
        if setup.setup():
            print("\n✅ Setup completed! You can now run:")
            print("   poetry run python tests/test_intent_routing.py")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
            
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're in the LifeBuddy directory and have installed dependencies:")
        print("  poetry install")
    except Exception as e:
        print(f"Setup error: {e}") 