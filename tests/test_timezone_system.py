#!/usr/bin/env python3
"""
Test script for timezone-aware health data system.
Verifies that timezone detection and database creation work correctly.
"""

import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_timezone_detection():
    """Test the timezone detection functionality."""
    print("🧪 Testing Timezone Detection")
    print("=" * 40)
    
    try:
        from app.ingestion.apple_health import get_user_timezone
        
        # Test timezone detection
        user_tz = get_user_timezone()
        
        print(f"✅ Timezone detection successful!")
        print(f"   Name: {user_tz['name']}")
        print(f"   Offset: {user_tz['offset']}")
        print(f"   Type: {type(user_tz['tzinfo'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Timezone detection failed: {e}")
        return False


def test_database_creation():
    """Test timezone-aware database creation."""
    print("\n🧪 Testing Database Creation")
    print("=" * 40)
    
    try:
        from app.ingestion.apple_health import AppleHealthParser
        import sqlite3
        
        # Create a test database
        test_db_path = "data/test_timezone.db"
        
        # Remove existing test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        # Create parser instance (this will detect timezone)
        parser = AppleHealthParser("dummy_path.xml", test_db_path)
        
        # Create database (without parsing XML)
        parser.create_database()
        
        # Verify database structure
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # Check if user_settings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
        if not cursor.fetchone():
            raise Exception("user_settings table not created")
        
        # Check if timezone data was inserted
        cursor.execute("SELECT timezone_name, timezone_offset FROM user_settings WHERE id = 1")
        result = cursor.fetchone()
        
        if not result:
            raise Exception("Timezone data not inserted")
        
        print(f"✅ Database creation successful!")
        print(f"   Database: {test_db_path}")
        print(f"   Stored timezone: {result[0]} ({result[1]})")
        
        # Check all expected tables exist
        expected_tables = ['user_settings', 'health_records', 'daily_summaries', 'workouts']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = [t for t in expected_tables if t not in tables]
        if missing_tables:
            raise Exception(f"Missing tables: {missing_tables}")
        
        print(f"   All expected tables created: {', '.join(expected_tables)}")
        
        conn.close()
        
        # Clean up test database
        os.remove(test_db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False


def test_health_service():
    """Test the health data service timezone functionality."""
    print("\n🧪 Testing Health Data Service")
    print("=" * 40)
    
    try:
        # Check if main database exists
        main_db_path = "data/lifebuddy.db"
        if not os.path.exists(main_db_path):
            print("⚠️ Main database not found, skipping service test")
            print("   Run Apple Health parser first to create the database")
            return True
        
        from app.core.health_data_service import HealthDataService
        
        # Create service instance
        service = HealthDataService()
        
        # Test timezone info retrieval
        timezone_info = service.get_user_timezone_info()
        
        print(f"✅ Health service timezone test successful!")
        print(f"   {timezone_info['message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health service test failed: {e}")
        return False


def main():
    """Run all timezone system tests."""
    print("🌍 LifeBuddy Timezone-Aware System Test")
    print("=" * 50)
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    tests = [
        ("Timezone Detection", test_timezone_detection),
        ("Database Creation", test_database_creation),
        ("Health Service", test_health_service),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Timezone system is working correctly.")
        print("\nNext steps:")
        print("1. Run Apple Health parser to create timezone-aware database:")
        print("   python app/ingestion/apple_health.py")
        print("2. Test the LLM agents with timezone-aware data:")
        print("   poetry run python tests/test_intent_routing.py")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 