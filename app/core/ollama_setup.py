"""
Automatic Ollama setup for LifeBuddy.
Handles installation, server startup, and model downloading.
"""
import os
import sys
import time
import subprocess
import platform
import requests
from pathlib import Path


class OllamaSetup:
    """Automated Ollama setup and management."""
    
    def __init__(self):
        self.default_model = "llama3.2:3b"
        self.base_url = "http://localhost:11434"
        self.system = platform.system().lower()
    
    def is_ollama_installed(self) -> bool:
        """Check if Ollama is already installed."""
        try:
            result = subprocess.run(["ollama", "--version"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def is_ollama_running(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def install_ollama(self):
        """Install Ollama based on the operating system."""
        if self.is_ollama_installed():
            print("✅ Ollama is already installed")
            return True
        
        print("📦 Installing Ollama...")
        
        try:
            if self.system == "darwin":  # macOS
                # Download and install Ollama for macOS
                subprocess.run([
                    "curl", "-fsSL", 
                    "https://ollama.ai/install.sh"
                ], check=True, stdout=subprocess.PIPE)
                subprocess.run(["sh"], input=open("/tmp/ollama_install.sh").read(), 
                             text=True, check=True)
                
            elif self.system == "linux":
                # Linux installation
                subprocess.run([
                    "curl", "-fsSL", "https://ollama.ai/install.sh", "|", "sh"
                ], shell=True, check=True)
                
            elif self.system == "windows":
                print("❌ Windows auto-install not supported yet.")
                print("Please download Ollama from: https://ollama.ai/download")
                return False
            
            print("✅ Ollama installed successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Ollama: {e}")
            return False
    
    def start_ollama_server(self):
        """Start Ollama server in the background."""
        if self.is_ollama_running():
            print("✅ Ollama server is already running")
            return True
        
        print("🚀 Starting Ollama server...")
        
        try:
            # Start server in background
            if self.system in ["darwin", "linux"]:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # Wait for server to start
            for i in range(10):
                time.sleep(2)
                if self.is_ollama_running():
                    print("✅ Ollama server started successfully!")
                    return True
                print(f"⏳ Waiting for server... ({i+1}/10)")
            
            print("❌ Failed to start Ollama server")
            return False
            
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    def pull_model(self, model_name: str | None = None):
        """Download the specified model."""
        model = model_name or self.default_model
        
        print(f"📥 Downloading model: {model}")
        print("This may take a few minutes...")
        
        try:
            result = subprocess.run(
                ["ollama", "pull", model],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ Model {model} downloaded successfully!")
                return True
            else:
                print(f"❌ Failed to download model: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error downloading model: {e}")
            return False
    
    def list_models(self):
        """List available models."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("📋 Available models:")
                print(result.stdout)
                return True
            else:
                print("❌ Failed to list models")
                return False
                
        except Exception as e:
            print(f"❌ Error listing models: {e}")
            return False
    
    def setup(self, model_name: str | None = None):
        """Complete Ollama setup process."""
        print("🤖 LifeBuddy Ollama Setup")
        print("=" * 30)
        
        # Step 1: Install Ollama
        if not self.install_ollama():
            return False
        
        # Step 2: Start server
        if not self.start_ollama_server():
            return False
        
        # Step 3: Download model
        if not self.pull_model(model_name):
            return False
        
        # Step 4: Verify setup
        print("\n🧪 Testing setup...")
        if self.test_model():
            print("\n🎉 Ollama setup completed successfully!")
            print(f"✅ Model '{model_name or self.default_model}' is ready to use")
            return True
        else:
            print("\n❌ Setup verification failed")
            return False
    
    def test_model(self, model_name: str | None = None):
        """Test if the model works."""
        model = model_name or self.default_model
        
        try:
            # Simple test query
            result = subprocess.run([
                "ollama", "run", model, 
                "Hello! Respond with just 'OK' if you can understand this."
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and "OK" in result.stdout.upper():
                return True
            else:
                print(f"Model test failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("Model test timed out")
            return False
        except Exception as e:
            print(f"Model test error: {e}")
            return False


def main():
    """Run Ollama setup."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Ollama for LifeBuddy")
    parser.add_argument("--model", default="llama3.2:3b", 
                       help="Model to download (default: llama3.2:3b)")
    parser.add_argument("--list", action="store_true", 
                       help="List available models")
    parser.add_argument("--test", action="store_true", 
                       help="Test current setup")
    
    args = parser.parse_args()
    
    setup = OllamaSetup()
    
    if args.list:
        setup.list_models()
    elif args.test:
        if setup.test_model():
            print("✅ Ollama is working correctly!")
        else:
            print("❌ Ollama test failed")
    else:
        setup.setup(args.model)


if __name__ == "__main__":
    main() 