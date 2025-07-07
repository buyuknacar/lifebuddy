"""
Test suite for LLM intent classification and agent routing.
Run this to test the intent classification and agent routing system.
"""
import os
import sys
from pathlib import Path

# Add app to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.agents.health_graph import health_graph
from app.core.logger import get_logger

# Initialize logger for test errors
logger = get_logger(__name__)

# Load environment variables
load_dotenv()


def test_intent_classification():
    """Test intent classification accuracy."""
    
    test_cases = [
        # FITNESS queries (default for greetings, workouts, goals)
        ("Hello, what can you help me with?", "fitness"),
        ("Create a workout plan for me", "fitness"),
        ("What exercises should I do for my bad knee?", "fitness"),
        ("How can I improve my sleep quality?", "fitness"),
        ("I'm feeling stressed, any advice?", "fitness"),
        ("What foods should I avoid for better health?", "fitness"),
        
        # HEALTH queries (Apple Health data analysis)
        ("How many steps did I take today?", "health"),
        ("What's my average heart rate during workouts?", "health"),
        ("Show me my running performance this week", "health"),
        ("Show me my health trends over the past month", "health"),
        ("Summarize my health data", "health"),
        ("Analyze my sleep patterns", "health")
    ]
    
    print("🧪 Testing Intent Classification")
    print("=" * 40)
    
    correct = 0
    total = len(test_cases)
    
    for query, expected_intent in test_cases:
        try:
            result = health_graph.chat(query)
            actual_intent = result['intent']
            is_correct = actual_intent == expected_intent
            
            if is_correct:
                correct += 1
                status = "✅"
            else:
                status = "❌"
            
            print(f"{status} '{query}' -> {actual_intent} (expected: {expected_intent})")
            
        except Exception as e:
            print(f"❌ Error processing '{query}': {e}")
    
    accuracy = (correct / total) * 100
    print(f"\n📊 Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    return accuracy


def test_agent_responses():
    """Test that each agent type produces reasonable responses."""
    
    test_queries = [
        "Hello, I'm ready to get fit!",
        "Create a workout plan for me", 
        "How many steps did I take today?",
        "Show me my weekly health summary"
    ]
    
    print("\n🤖 Testing Agent Responses")
    print("=" * 40)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 30)
        
        try:
            result = health_graph.chat(query)
            print(f"Intent: {result['intent']}")
            print(f"Agent: LangGraph Health Agent")
            print(f"Response: {result['response'][:200]}...")
            
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Run all tests."""
    print("🤖 LifeBuddy LLM System Tests\n")
    
    # Set default provider if not specified
    if not os.getenv("LLM_PROVIDER"):
        os.environ["LLM_PROVIDER"] = "ollama"
        print("📝 Using default provider: ollama")
    else:
        print(f"📝 Using provider: {os.getenv('LLM_PROVIDER')}")
    
    try:
        # Test intent classification
        accuracy = test_intent_classification()
        
        # Test agent responses
        test_agent_responses()
        
        print(f"\n🎉 Tests completed! Intent classification accuracy: {accuracy:.1f}%")
        
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        if "Connection refused" in str(e):
            print("\n🔧 Ollama is not running. Run automatic setup:")
            print("  poetry run python deployment/setup_ollama.py")
            print("\nThen try the test again:")


if __name__ == "__main__":
    main() 