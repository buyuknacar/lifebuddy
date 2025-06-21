# 🌟 LifeBuddy

**Your Personal AI Health & Wellness Companion**

LifeBuddy is an open-source, privacy-first health comapnion that transforms your Apple Health data into personalized insights using AI. Built with a "Bring Your Own API" architecture - use local models (free) or your own API keys for maximum privacy and control. Currently focused on health data analysis and tools, with planned expansion into comprehensive **personal fitness, diet, and wellness coaching**. All data stays local on your machine - no subscriptions, no data sharing, just intelligent health insights powered by your own data.


## 🚀 Development Phases

### **Phase 1: Health Analytics (Current MVP)**
**✅ Available Now:**
- 📊 **Apple Health Integration**: Import and analyze years of health data
- 🤖 **Health Analysis Tools**: AI-powered insights from your health metrics
- 💬 **Intelligent Chat**: Ask questions about your health data and trends
- 🔒 **Privacy-First**: All processing happens locally with multiple LLM providers
- 🐳 **Easy Deployment**: One-command Docker setup with automated Ollama

### **Phase 2: Comprehensive Wellness (Coming Soon)**
**🔮 Planned Features:**

**Diet & Nutrition:**
- 🥗 **Smart Diet Logging**: AI-assisted food entry and meal tracking
- 🍎 **LLM-Powered Food Entries**: Natural language food logging ("I had a turkey sandwich")
- 👨‍⚕️ **Dietitian Agent**: Personalized nutrition advice and meal planning
- 📈 **Nutrition Analytics**: Macro/micro tracking with health data correlations

**Fitness & Training:**
- 🏋️ **Gym Workout Plans**: AI-generated workout routines based on your goals
- 💪 **Progress Tracking**: Log weights, reps, and track strength gains over time
- 🏃‍♂️ **Trainer Agent**: Personal trainer persona for workout guidance and motivation
- 📊 **Performance Analytics**: Strength trends and workout optimization

**Wellness & Memory:**
- 📝 **Smart Journaling**: Daily mood, energy, and wellness entries
- 📚 **Journal Summaries**: AI-generated insights from your entries
- 🗓️ **Monthly Reflections**: Long-term pattern recognition and summarized insights
- 🧠 **Vector Memory**: Long-term memory integration for personalized conversations
- 👤 **Personal Profile**: Markdown-based profile for consistent AI interactions
- 🎯 **Goal Tracking**: Current and long-term goals alignment with AI coaching


## 🐳 Docker Setup (Recommended)

**Fully automated setup - everything handled for you:**

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd lifebuddy

# Install Docker Desktop (if not already installed)
# Download from: https://www.docker.com/products/docker-desktop/

# One-command setup and start (recommended)
./quick-start.sh

# Or manual setup:
# ./deployment/setup-ollama.sh
# cd deployment && docker compose up --build

# Open in browser
open http://localhost:8501
```

### Add Your Health Data (Optional)
1. Export health data from iPhone Health app
2. Save as `~/Downloads/export.xml` 
3. Restart container - data will be auto-processed

**What the setup script does:**
- ✅ Installs Ollama if not present
- ✅ Starts Ollama server automatically  
- ✅ Downloads the AI model (llama3.2:3b)
- ✅ Sets up auto-start on login (optional)
- ✅ Verifies everything is working

**Why this approach?** The container connects to Ollama running on your host machine, avoiding slow model downloads every time you start the container. This makes startup instant while keeping all your data local and secure.

---

## 🛠️ Advanced Setup (Developers)

### Local Development

```bash
# Install dependencies
poetry install

# Setup local AI (Ollama)
poetry run python deployment/setup_ollama.py

# Or with custom model
poetry run python deployment/setup_ollama.py --model llama3.2:1b

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

## 📊 Using LifeBuddy (Phase 1)

### Adding Your Apple Health Data

1. **Export from iPhone**: 
   - Open Health app → Profile → Export All Health Data
   - This creates a zip file with all your health data

2. **Import to LifeBuddy**:
   - **Docker users**: Save export.zip to Downloads folder (auto-detected!)
   - **Manual setup**: `python app/ingestion/apple_health.py path/to/export.zip`

### Current Capabilities

**Health Data Analysis:**
- **Step tracking**: "How many steps did I take this week?"
- **Heart rate insights**: "Show me my resting heart rate trends"
- **Sleep analysis**: "How has my sleep quality changed over time?"
- **Activity patterns**: "What are my most active days?"
- **Health correlations**: "How does my sleep affect my heart rate?"

**Interactive Chat:**
- **Data exploration**: "What health metrics do you have for me?"
- **Trend analysis**: "Show me my health trends over the past month"
- **Comparative insights**: "How does this year compare to last year?"
- **General conversation**: Ask questions about your health journey

## 🔧 Configuration

### AI Provider Setup

**Option 1: Local (Recommended)**
```bash
# Default setup - no API keys needed
./quick-start.sh
# Uses Ollama locally - completely free and private
```

**Option 2: Bring Your Own API**
```bash
# Add your API keys to docker-compose.yml or environment:
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
export GOOGLE_API_KEY="your-key-here"

# Then select your preferred provider in the Streamlit interface
```

**Why Bring Your Own API?**
- 🔒 **Maximum Privacy**: Your API keys, your control
- 💰 **Transparent Costs**: See exactly what you're paying for
- 🚫 **No Middleman**: Direct relationship with AI providers
- 🎛️ **Full Control**: Choose models, rate limits, and usage patterns

## 🐳 Docker Details

For more Docker configuration options, see [DOCKER.md](deployment/DOCKER.md).

## 📋 System Requirements

- **For Docker**: 4GB+ RAM, Docker Desktop
- **For Manual Setup**: Python 3.9+, Poetry
- **For Ollama**: 8GB+ RAM recommended

