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

## 🚀 Quick Setup

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

**Built with ❤️ for health-conscious individuals who value privacy and personalization.**
