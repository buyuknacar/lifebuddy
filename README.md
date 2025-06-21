# 🌟 LifeBuddy

**Your Personal AI Health & Wellness Companion**

LifeBuddy is an open-source, privacy-first health analytics platform that transforms your Apple Health data into personalized fitness, diet, and wellness insights using AI. Track your workouts, analyze your nutrition patterns, journal your thoughts, and receive personalized coaching - all while keeping your health data completely private and running locally on your machine. No subscriptions, no data sharing, just intelligent health insights powered by your own data.

## 🎯 Key Features

- 🏃 **Fitness Tracking**: Analyze workout patterns and performance trends
- 🥗 **Diet Insights**: Understand your nutrition habits and correlations
- 📝 **Health Journaling**: Track mood, energy, and wellness notes
- 🤖 **Personalized AI Coaching**: Get tailored advice based on your unique data
- 🔒 **Privacy First**: Supporting Local Models
- 🆓 **Open Source**: Free forever, community-driven development

## 🚀 Quick Start (Recommended)

### For Everyone (Mac/Windows/Linux)

1. **Install Docker Desktop**: Download from [docker.com](https://www.docker.com/products/docker-desktop/)

2. **Run LifeBuddy**:
   ```bash
   docker-compose up --build
   ```

3. **Open in your browser**: http://localhost:8501

4. **Optional - Add your health data**:
   - Export your Apple Health data (Health app → Profile → Export All Health Data)
   - Save the export.zip to your Downloads folder
   - LifeBuddy will automatically detect and process it!

That's it! 🎉

---

## 🛠️ Advanced Setup (Developers)

### Local Development

```bash
# Install dependencies
poetry install

# Setup local AI (Ollama)
poetry run python setup_ollama.py

# Or with custom model
poetry run python setup_ollama.py --model llama3.2:1b

# Test the system
poetry run python tests/test_intent_routing.py
```

**Available setup options:**
- `--model MODEL_NAME` - Choose different model (default: llama3.2:3b)
- `--list` - List available models
- `--test` - Test current setup

### Manual FastAPI + Streamlit

```bash
# Terminal 1 - Start FastAPI backend
poetry run python -m app.api.main

# Terminal 2 - Start Streamlit frontend  
poetry run streamlit run app/ui/streamlit_app.py
```

## 📊 Using LifeBuddy

### Adding Your Health Data

1. **Export from iPhone**: 
   - Open Health app → Profile → Export All Health Data
   - This creates a zip file with all your health data

2. **Import to LifeBuddy**:
   - **Docker users**: Save export.zip to Downloads folder (auto-detected!)
   - **Manual setup**: `python app/ingestion/apple_health.py path/to/export.zip`

### Chat Interface

- **General conversation**: "Hello, how are you?"
- **Health analysis**: "Show me my recent activity" or "How's my fitness?"
- **Specific queries**: "What were my steps yesterday?" or "Analyze my workouts"

## 🔧 Configuration

### AI Model Providers

LifeBuddy supports multiple AI providers:

- **Ollama** (default, runs locally, free)
- **OpenAI** (requires API key)
- **Anthropic Claude** (requires API key)
- **Google Gemini** (requires API key)

Select your preferred provider in the Streamlit interface.

## 🐳 Docker Details

For more Docker configuration options, see [DOCKER.md](DOCKER.md).

## 📋 System Requirements

- **For Docker**: 4GB+ RAM, Docker Desktop
- **For Manual Setup**: Python 3.9+, Poetry
- **For Ollama**: 8GB+ RAM recommended

