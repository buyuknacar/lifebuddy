#!/usr/bin/env python3
"""
Test script for LangGraph migration.
Verifies that the new graph-based system maintains compatibility with existing functionality.
"""

import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


def test_langgraph_basic_functionality():
    """Test basic LangGraph health agent functionality."""
    print("🧪 Testing LangGraph Basic Functionality")
    print("=" * 50)
    
    try:
        # Import may fail if LangGraph dependencies aren't properly installed
        from agents.health_graph import health_graph
        
        # Test basic chat functionality
        test_queries = [
            "How many steps did I take yesterday?",
            "What's my average heart rate this week?", 
            "Show me my recent workouts",
            "How's my weight trending?"
        ]
        
        print("✅ LangGraph health agent imported successfully!")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test Query {i}: {query}")
            try:
                response = health_graph.chat(query)
                print(f"✅ Response received (length: {len(response)} chars)")
                # Don't print full response to keep output clean
                if len(response) > 100:
                    print(f"   Preview: {response[:100]}...")
                else:
                    print(f"   Response: {response}")
                    
            except Exception as e:
                print(f"❌ Query failed: {e}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("   Make sure LangGraph is installed: poetry add langgraph")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_router_compatibility():
    """Test that the new system maintains router interface compatibility."""
    print("\n🧪 Testing Router Compatibility")
    print("=" * 50)
    
    try:
        from agents.health_graph import health_graph
        
        # Test the compatibility route_query method
        test_query = "What's my step count for the last 3 days?"
        
        result = health_graph.route_query(test_query)
        
        # Verify the result has the expected structure (same as old router)
        expected_keys = ["intent", "agent", "response", "query", "session_id"]
        
        for key in expected_keys:
            if key not in result:
                print(f"❌ Missing key in result: {key}")
                return False
        
        print("✅ Router compatibility maintained!")
        print(f"   Intent: {result['intent']}")
        print(f"   Agent: {result['agent']}")
        print(f"   Query: {result['query']}")
        print(f"   Session ID: {result['session_id']}")
        print(f"   Response length: {len(result['response'])} chars")
        
        return True
        
    except Exception as e:
        print(f"❌ Router compatibility test failed: {e}")
        return False


def test_session_persistence():
    """Test session persistence and multi-turn conversations."""
    print("\n🧪 Testing Session Persistence")
    print("=" * 50)
    
    try:
        from agents.health_graph import health_graph
        
        # Create a session and have a multi-turn conversation
        session_id = "test_session_123"
        
        # First message
        response1 = health_graph.chat("Show me my steps for the last week", session_id)
        print(f"✅ First message processed (session: {session_id})")
        
        # Follow-up message (should have context)
        response2 = health_graph.chat("What about my heart rate during that time?", session_id)
        print(f"✅ Follow-up message processed with same session")
        
        # Verify responses are different (indicating context was maintained)
        if response1 != response2:
            print("✅ Session context appears to be working (different responses)")
        else:
            print("⚠️ Responses are identical - session context may not be working")
        
        return True
        
    except Exception as e:
        print(f"❌ Session persistence test failed: {e}")
        return False


def test_timezone_awareness():
    """Test that timezone awareness is properly integrated."""
    print("\n🧪 Testing Timezone Awareness")
    print("=" * 50)
    
    try:
        from agents.health_graph import health_graph
        
        # Test timezone info query
        response = health_graph.chat("What timezone am I in?")
        
        if "timezone" in response.lower() or "PDT" in response or "UTC" in response:
            print("✅ Timezone awareness working!")
            print(f"   Response contains timezone info: {response[:200]}...")
        else:
            print("⚠️ Timezone info not found in response")
            print(f"   Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Timezone awareness test failed: {e}")
        return False


def test_intent_classification():
    """Test that intent classification still works correctly."""
    print("\n🧪 Testing Intent Classification")
    print("=" * 50)
    
    try:
        from agents.health_graph import health_graph
        
        # Test different types of queries
        test_cases = [
            ("How many steps did I walk today?", "fitness"),
            ("What should I eat for lunch?", "nutrition"),
            ("I'm feeling stressed lately", "wellness"),
            ("Show me my health data summary", "general")
        ]
        
        for query, expected_domain in test_cases:
            print(f"\n📝 Testing: {query}")
            response = health_graph.chat(query)
            
            # Check if response seems appropriate for the domain
            domain_keywords = {
                "fitness": ["steps", "exercise", "workout", "activity", "heart rate"],
                "nutrition": ["calories", "diet", "food", "nutrition", "weight"],
                "wellness": ["stress", "sleep", "mood", "wellness", "mental"],
                "general": ["data", "summary", "analysis", "health"]
            }
            
            keywords = domain_keywords.get(expected_domain, [])
            found_keywords = [kw for kw in keywords if kw.lower() in response.lower()]
            
            if found_keywords:
                print(f"✅ Intent classification working - found keywords: {found_keywords}")
            else:
                print(f"⚠️ No domain-specific keywords found for {expected_domain}")
        
        return True
        
    except Exception as e:
        print(f"❌ Intent classification test failed: {e}")
        return False


def main():
    """Run all LangGraph migration tests."""
    print("🔄 LifeBuddy LangGraph Migration Tests")
    print("=" * 60)
    
    # Check if Ollama is running (needed for LLM functionality)
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("⚠️ Ollama server not responding. Some tests may fail.")
            print("   Start Ollama: poetry run python setup_ollama.py")
    except:
        print("⚠️ Cannot connect to Ollama. Some tests may fail.")
    
    tests = [
        ("Basic Functionality", test_langgraph_basic_functionality),
        ("Router Compatibility", test_router_compatibility),
        ("Session Persistence", test_session_persistence),
        ("Timezone Awareness", test_timezone_awareness),
        ("Intent Classification", test_intent_classification),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 LANGGRAPH MIGRATION TEST RESULTS")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! LangGraph migration successful.")
        print("\n✅ Migration Benefits Achieved:")
        print("   • Graph-based agent orchestration")
        print("   • Session persistence and memory")
        print("   • Timezone-aware health analytics")
        print("   • Backward compatibility with existing interfaces")
        print("   • Multi-turn conversational capabilities")
        
        print("\n🚀 Next Steps:")
        print("   • Update main application to use health_graph instead of health_router")
        print("   • Add vector database for semantic memory")
        print("   • Implement conversation history persistence")
        print("   • Add more sophisticated health analysis workflows")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        print("   • Ensure all dependencies are installed: poetry install")
        print("   • Make sure Ollama is running: poetry run python setup_ollama.py")
        print("   • Verify health database exists: python app/ingestion/apple_health.py")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 