#!/usr/bin/env python3
"""
Quick registration test script.
Run this after setting up your SUPABASE_SERVICE_ROLE_KEY in .env
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_client import register_user, authenticate_user

def test_registration():
    print("🧪 Testing User Registration & Authentication")
    print("=" * 50)

    # Get user input
    email = input("Enter email for test user: ").strip()
    password = input("Enter password for test user: ").strip()

    if not email or not password:
        print("❌ Email and password are required")
        return False

    print(f"\n📝 Registering user: {email}")

    # Test registration
    success, message = register_user(email, password)
    print(f"Registration result: {'✅' if success else '❌'} {message}")

    if not success:
        return False

    print(f"\n🔐 Testing login for: {email}")

    # Test authentication
    auth_success, user_data = authenticate_user(email, password)
    print(f"Authentication result: {'✅' if auth_success else '❌'}")

    if auth_success:
        print("User data:", user_data)
        print("\n🎉 SUCCESS! User registration and authentication working!")
        print("You can now login through the web interface.")
        return True
    else:
        print(f"Authentication failed: {user_data}")
        return False

if __name__ == "__main__":
    success = test_registration()
    sys.exit(0 if success else 1)