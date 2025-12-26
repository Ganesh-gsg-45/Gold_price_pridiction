#!/usr/bin/env python3
"""
Quick verification script to check if your service role key is working.
Run this after updating your .env file with the real service role key.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_client import get_supabase_client, SUPABASE_SERVICE_ROLE_KEY

def verify_service_key():
    print("🔐 Verifying Service Role Key Configuration")
    print("=" * 45)

    # Check if key is configured
    if not SUPABASE_SERVICE_ROLE_KEY or SUPABASE_SERVICE_ROLE_KEY == 'your_service_role_key_here':
        print("❌ Service role key not configured or still placeholder")
        print("   Please update your .env file with the real key from Supabase")
        return False

    print("✅ Service role key is configured")

    # Test service role client
    print("\n🔗 Testing Supabase connection with service role key...")
    client = get_supabase_client(use_service_role=True)

    if not client:
        print("❌ Failed to create Supabase client with service role key")
        return False

    # Test database access
    try:
        # Try to select from users table
        result = client.table('users').select('*').limit(1).execute()
        print("✅ Service role key working - can access users table")
        print(f"   Current users in database: {len(result.data)}")
        return True
    except Exception as e:
        print(f"❌ Service role key test failed: {e}")
        print("   Make sure the key is correct and the users table exists")
        return False

if __name__ == "__main__":
    success = verify_service_key()
    if success:
        print("\n🎉 Service role key is working!")
        print("   You can now register users and they will be saved to Supabase.")
    else:
        print("\n❌ Service role key needs to be fixed.")
        print("   Follow the instructions to get the correct key from Supabase.")
    sys.exit(0 if success else 1)