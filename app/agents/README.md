# LifeBuddy LLM Agents

## Overview

The LifeBuddy agent system uses **intent classification** and **specialized routing** to provide personalized health insights.

## Supported LLM Providers

### Open Source (Recommended)
- **Ollama**: Local models, privacy-first, free
  ```bash
  # Automatic setup (Windows/macOS/Linux)
  poetry run python deployment/setup_ollama.py
  
  # Or manual install:
  # Windows: Download from https://ollama.ai/download
  # macOS/Linux: curl -fsSL https://ollama.ai/install.sh | sh
  ```

### API Providers
- **OpenAI**: GPT models
- **Anthropic**: Claude models  
- **Google**: Gemini models
- **Azure**: Azure OpenAI

## Quick Start

```bash
# Setup Ollama (recommended)
poetry run python deployment/setup_ollama.py

# Test the agents
poetry run python tests/test_intent_routing.py
```

## Configuration

Set your provider in environment variables:

```bash
# For Ollama (default)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b

# For OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

# For Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

## Agent Types

1. **Fitness Agent**: Exercise, workouts, activity tracking
2. **Nutrition Agent**: Diet, calories, weight management  
3. **Wellness Agent**: Sleep, stress, mood, mental health
4. **General Agent**: Data analysis, trends, correlations

## Usage

```python
from app.agents.router import health_router

# Route a query automatically
result = health_router.route_query("How many steps did I take today?")
print(f"Intent: {result['intent']}")      # "fitness"
print(f"Agent: {result['agent']}")        # "Fitness Agent"
print(f"Response: {result['response']}")  # AI response
```

## Testing

```bash
# Test the intent classification and routing system
poetry run python tests/test_intent_routing.py
``` 