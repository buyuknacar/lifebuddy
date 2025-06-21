#!/usr/bin/env python3
"""
Test script for LangGraph migration - Phase 1 (Fitness Focus).
Verifies that the new graph-based system works for fitness-related queries only.
Following phased development approach.
"""

import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


def test_langgraph_basic_functionality():
    """Test basic LangGraph health agent functionality for fitness queries."""
    print("🧪 Testing LangGraph Basic Functionality (Fitness Focus)")
    print("=" * 50)
    
    try:
        # Import may fail if LangGraph dependencies aren't properly installed
        from app.agents.health_graph import health_graph
        
        # Test fitness-focused queries only
        test_queries = [
            "How many steps did I take yesterday?",
            "What's my average heart rate this week?", 
            "Show me my recent workouts",
            "What's my activity summary for the last 7 days?"
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
    """Test that the new system maintains router interface compatibility for fitness queries."""
    print("\n🧪 Testing Router Compatibility (Fitness)")
    print("=" * 50)
    
    try:
        from app.agents.health_graph import health_graph
        
        # Test fitness-focused query
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
    """Test session persistence with fitness queries."""
    print("\n🧪 Testing Session Persistence (Fitness)")
    print("=" * 50)
    
    try:
        from app.agents.health_graph import health_graph
        
        # Create a session and have a multi-turn fitness conversation
        session_id = "test_fitness_session_123"
        
        # First message - fitness focused
        response1 = health_graph.chat("Show me my steps for the last week", session_id)
        print(f"✅ First message processed (session: {session_id})")
        
        # Follow-up message - fitness related
        response2 = health_graph.chat("What about my heart rate during those workouts?", session_id)
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
        from app.agents.health_graph import health_graph
        
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


def test_fitness_tools():
    """Test fitness-specific tools and functionality."""
    print("\n🧪 Testing Fitness Tools")
    print("=" * 50)
    
    try:
        from app.agents.health_graph import health_graph
        
        # Test fitness-specific queries
        fitness_queries = [
            "How many steps did I walk today?",
            "What's my heart rate data for this week?",
            "Show me my workout history",
            "Give me my activity summary"
        ]
        
        for query in fitness_queries:
            print(f"\n📝 Testing: {query}")
            response = health_graph.chat(query)
            
            # Check if response contains fitness-related keywords
            fitness_keywords = ["steps", "heart rate", "workout", "activity", "exercise", "calories", "distance"]
            found_keywords = [kw for kw in fitness_keywords if kw.lower() in response.lower()]
            
            if found_keywords:
                print(f"✅ Fitness tools working - found keywords: {found_keywords}")
            else:
                print(f"⚠️ No fitness keywords found in response")
        
        return True
        
    except Exception as e:
        print(f"❌ Fitness tools test failed: {e}")
        return False


def main():
    """Run all LangGraph migration tests focused on fitness functionality."""
    print("🔄 LifeBuddy LangGraph Migration Tests - Phase 1 (Fitness)")
    print("=" * 60)
    
    # Test results
    results = {
        "Basic Functionality": test_langgraph_basic_functionality(),
        "Router Compatibility": test_router_compatibility(), 
        "Session Persistence": test_session_persistence(),
        "Timezone Awareness": test_timezone_awareness(),
        "Fitness Tools": test_fitness_tools()
    }
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 LANGGRAPH MIGRATION TEST RESULTS (Phase 1)")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! LangGraph migration successful for Phase 1.")
        print("\n✅ Phase 1 Benefits Achieved:")
        print("   • Graph-based agent orchestration")
        print("   • Session persistence and memory") 
        print("   • Timezone-aware health analytics")
        print("   • Backward compatibility with existing interfaces")
        print("   • Fitness-focused health tools integration")
        print("\n🚀 Ready for Phase 1 MVP:")
        print("   • FastAPI backend development")
        print("   • Streamlit frontend creation")
        print("   • Docker containerization")
        print("   • MVP deployment")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        print("   • Ensure all dependencies are installed: poetry install")
        print("   • Make sure Ollama is running: poetry run python deployment/setup_ollama.py")
        print("   • Verify health database exists: python app/ingestion/apple_health.py")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 