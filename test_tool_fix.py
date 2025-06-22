#!/usr/bin/env python3
"""
Quick test to verify tool calling fixes for small models.
"""
import requests
import json
import time

def test_tool_calling():
    """Test the heart rate tool that was failing."""
    
    print("🧪 Testing LifeBuddy Tool Calling Fixes")
    print("=" * 50)
    
    # Wait for API to be ready
    print("⏳ Waiting for API to start...")
    for i in range(30):
        try:
            response = requests.get("http://localhost:8000/health/status", timeout=5)
            if response.status_code == 200:
                print("✅ API is ready!")
                break
        except:
            pass
        time.sleep(1)
        if i == 29:
            print("❌ API failed to start")
            return
    
    # Test the problematic query
    test_queries = [
        "tell me about my heart rate summary",
        "show my heart rate for last 7 days", 
        "get my steps",
        "analyze my sleep"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        
        try:
            response = requests.post(
                "http://localhost:8000/chat",
                json={
                    "message": query,
                    "session_id": "test-session"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response: {data['response'][:100]}...")
                
                # Check if tools were used
                thinking_chain = data.get('thinking_chain', [])
                if thinking_chain:
                    print(f"🔧 Tools used: {[step.get('tool_name') for step in thinking_chain]}")
                else:
                    print("⚠️  No tools used (fallback response)")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    test_tool_calling() 