#!/usr/bin/env python3
"""
Test script to verify Supabase user registration is working properly.
Run this after adding SUPABASE_SERVICE_ROLE_KEY to your .env file.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_client import register_user, authenticate_user, get_supabase_client

def test_supabase_registration():
    print("🔍 Testing Supabase User Registration")
    print("=" * 40)

    # Test 1: Check Supabase connection
    print("1. Testing Supabase connection...")
    client = get_supabase_client(use_service_role=True)  # Use service role for admin operations
    if not client:
        print("❌ Supabase client not available")
        return False

    try:
        # Test basic connectivity
        result = client.table('users').select('*').limit(1).execute()
        print("✅ Supabase connection successful")
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

    # Test 2: Register a test user
    print("\n2. Testing user registration...")
    import time
    test_email = f"test_user_{int(time.time())}@example.com"  # Unique email each time
    test_password = "test_password_123"

    success, message = register_user(test_email, test_password)
    if success and "temporary storage" not in message:
        print("✅ User registration successful in Supabase")
    else:
        print(f"❌ User registration failed: {message}")
        return False

    # Test 3: Verify user exists in Supabase
    print("\n3. Verifying user exists in Supabase...")
    try:
        result = client.table('users').select('*').eq('email', test_email).execute()
        print(f"DEBUG: Supabase result: {result}")
        print(f"DEBUG: Result data: {result.data}")
        if result.data:
            print("✅ User found in Supabase database")
            print(f"   User ID: {result.data[0].get('id', 'N/A')}")
            print(f"   Email: {result.data[0].get('email', 'N/A')}")
            print(f"   All columns: {list(result.data[0].keys())}")
        else:
            print("❌ User not found in Supabase")
            return False
    except Exception as e:
        print(f"❌ Error checking user in Supabase: {e}")
        return False

    # Test 4: Test authentication
    print("\n4. Testing user authentication...")
    auth_success, user_data = authenticate_user(test_email, test_password)
    if auth_success:
        print("✅ User authentication successful")
    else:
        print(f"❌ User authentication failed: {user_data}")
        return False

    print("\n🎉 All tests passed! Supabase integration is working correctly.")
    print("\nNext steps:")
    print("- Remove the test user from your database if needed")
    print("- Your app will now save users to Supabase instead of temporary storage")

    return True

if __name__ == "__main__":
    success = test_supabase_registration()
    sys.exit(0 if success else 1)