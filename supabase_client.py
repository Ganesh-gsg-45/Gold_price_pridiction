import os
from datetime import timedelta, datetime
import bcrypt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try to import supabase, but handle failures gracefully
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Supabase import failed: {e}")
    print("Using fallback in-memory storage for user authentication")
    SUPABASE_AVAILABLE = False
    create_client = None

# Load Supabase credentials from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://rqzqxljtkayndylskvdt.supabase.co')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJxenF4bGp0a2F5bmR5bHNrdmR0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU4ODgzMDUsImV4cCI6MjA4MTQ2NDMwNX0.ELfB7cD6QpL8FiL2Gd3K5euQC3QP_c2sgT6SQ9nUs60')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

# Validate that we have the required environment variables
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("⚠️ Supabase credentials not found in environment variables")
    print("Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file")
    SUPABASE_AVAILABLE = False

# For now, use a simple in-memory storage as fallback
users_db = {}

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    """Check password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def get_supabase_client(use_service_role=False):
    """Get a Supabase client instance"""
    if not SUPABASE_AVAILABLE:
        return None
    try:
        if use_service_role and SUPABASE_SERVICE_ROLE_KEY:
            return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        else:
            return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        print(f"Failed to create Supabase client: {e}")
        return None

def register_user(email, password, username=None):
    """Register a new user"""
    # Debug: Print service role key status
    print(f"🔍 SUPABASE_SERVICE_ROLE_KEY loaded: {'Yes' if SUPABASE_SERVICE_ROLE_KEY else 'No'}")
    print(f"🔍 Key length: {len(SUPABASE_SERVICE_ROLE_KEY) if SUPABASE_SERVICE_ROLE_KEY else 0}")

    # Check if we have service role key for registration
    if not SUPABASE_SERVICE_ROLE_KEY:
        print("⚠️ SUPABASE_SERVICE_ROLE_KEY not configured in .env file")
        print("   User registration will use temporary storage")
        print("   To fix: Add SUPABASE_SERVICE_ROLE_KEY to your .env file")
        print("   Get it from: Supabase Dashboard > Settings > API > service_role key")
    else:
        supabase = get_supabase_client(use_service_role=True)  # Use service role for registration

        if supabase:
            try:
                # Check if user exists
                existing = supabase.table("users").select("*").eq("email", email).execute()
                if existing.data:
                    return False, "User already exists"

                # Hash password
                hashed = hash_password(password)

                # Insert user
                user_data = {
                    "email": email,
                    "password_hash": hashed,
                    "created_at": datetime.now().isoformat(),
                    "username": username or email.split('@')[0]  # Use email prefix if no username provided
                }

                result = supabase.table("users").insert(user_data).execute()

                return True, "User registered successfully"
            except Exception as e:
                print(f"Supabase registration failed: {e}")
                print("Falling back to temporary storage")

    # Fallback to in-memory storage
    if email in users_db:
        return False, "User already exists"

    users_db[email] = {
        'password_hash': hash_password(password),
        'created_at': datetime.now().isoformat(),
        'id': len(users_db) + 1,
        'username': username
    }
    print("⚠️ Using in-memory storage (data will be lost on restart)")
    return True, "User registered successfully (temporary storage)"

def authenticate_user(email, password):
    """Authenticate user login"""
    supabase = get_supabase_client(use_service_role=True)  # Use service role for admin operations

    if supabase:
        try:
            user = supabase.table("users").select("*").eq("email", email).execute()
            if not user.data:
                return False, "User not found"

            user_data = user.data[0]
            if check_password(password, user_data['password_hash']):
                return True, user_data
            else:
                return False, "Invalid password"
        except Exception as e:
            print(f"Supabase authentication failed: {e}")
            # Fall through to in-memory storage

    # Fallback to in-memory storage
    if email in users_db:
        user_data = users_db[email]
        if check_password(password, user_data['password_hash']):
            return True, {
                'id': user_data['id'],
                'email': email,
                'created_at': user_data['created_at']
            }
    return False, "Authentication failed"

def save_today_price(karat, price):
    """Save today's price to database (optional)"""
    supabase = get_supabase_client()
    if not supabase:
        print("⚠️ Supabase not available, skipping price save")
        return

    try:
        supabase.table("gold_price").insert({
            "timestamp": datetime.now().isoformat(),
            "karat": karat,
            "price_per_gram": price
        }).execute()
    except Exception as e:
        print(f"⚠️ Failed to save price to database: {e}")

def save_predictions(karat, predictions):
    """Save predictions to database (optional)"""
    supabase = get_supabase_client()
    if not supabase:
        print("⚠️ Supabase not available, skipping predictions save")
        return

    try:
        for i, price in enumerate(predictions, 1):
            supabase.table("gold_prediction").insert({
                "prediction_date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                "karat": karat,
                "predicted_price": price
            }).execute()
    except Exception as e:
        print(f"⚠️ Failed to save predictions to database: {e}")
      
