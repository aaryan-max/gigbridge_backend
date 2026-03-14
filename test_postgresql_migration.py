#!/usr/bin/env python3
"""
PostgreSQL Migration Test Script for GigBridge
Tests the migration from SQLite to PostgreSQL
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def test_connection():
    """Test PostgreSQL connection"""
    print("Testing PostgreSQL connection...")
    try:
        from postgres_config import get_postgres_connection
        conn = get_postgres_connection()
        print("✅ PostgreSQL connection successful")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_table_creation():
    """Test table creation"""
    print("Testing table creation...")
    try:
        from database import create_tables
        create_tables()
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return False

def test_basic_operations():
    """Test basic database operations"""
    print("Testing basic operations...")
    try:
        from database import client_db, freelancer_db
        
        # Test client operations
        conn = client_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM client")
        client_count = cur.fetchone()[0]
        conn.close()
        
        # Test freelancer operations
        conn = freelancer_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM freelancer")
        freelancer_count = cur.fetchone()[0]
        conn.close()
        
        print(f"✅ Found {client_count} clients and {freelancer_count} freelancers")
        return True
    except Exception as e:
        print(f"❌ Basic operations failed: {e}")
        return False

def test_full_text_search():
    """Test PostgreSQL full-text search"""
    print("Testing full-text search...")
    try:
        from database import freelancer_db
        
        conn = freelancer_db()
        cur = conn.cursor()
        
        # Test search index exists
        cur.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'freelancer_search' 
            AND indexname = 'freelancer_search_text_idx'
        """)
        index_exists = cur.fetchone()
        
        if index_exists:
            print("✅ Full-text search index exists")
        else:
            print("⚠️  Full-text search index not found (will be created on first search)")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Full-text search test failed: {e}")
        return False

def test_api_endpoints():
    """Test key API endpoints"""
    print("Testing API endpoints...")
    try:
        import requests
        base_url = "http://localhost:5000"
        
        # Test freelancers endpoint
        response = requests.get(f"{base_url}/freelancers/all", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ /freelancers/all returned {len(data.get('results', []))} results")
        else:
            print(f"❌ /freelancers/all failed with status {response.status_code}")
            return False
        
        return True
    except requests.exceptions.ConnectionError:
        print("⚠️  Flask server not running - start it with 'python app.py'")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def check_environment():
    """Check environment variables"""
    print("Checking environment variables...")
    
    required_vars = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\nSet these variables:")
        print("export POSTGRES_HOST=localhost")
        print("export POSTGRES_PORT=5432")
        print("export POSTGRES_DB=gigbridge")
        print("export POSTGRES_USER=gigbridge_user")
        print("export POSTGRES_PASSWORD=your_password")
        return False
    else:
        print("✅ All environment variables set")
        return True

def main():
    print("GigBridge PostgreSQL Migration Test")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", check_environment),
        ("Database Connection", test_connection),
        ("Table Creation", test_table_creation),
        ("Basic Operations", test_basic_operations),
        ("Full-Text Search", test_full_text_search),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 Migration test completed successfully!")
        return 0
    else:
        print("🚨 Some tests failed - check the issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
