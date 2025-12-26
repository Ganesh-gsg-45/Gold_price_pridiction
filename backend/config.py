"""
Application Configuration
"""

import os
import secrets
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    # Generate secure secret key if not provided
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_hex(32)
    DEBUG = False
    TESTING = False

    # Required API Keys - will be validated
    GOLDAPI_KEY = os.getenv('GOLDAPI_KEY')
    METALS_API_KEY = os.getenv('METALS_API_KEY')
    ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')

    # Supabase configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    # Gold purities
    GOLD_PURITIES = {
        '24K': 1.0,
        '22K': 0.916,
        '18K': 0.750,
        '14K': 0.583
    }

    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        required_vars = []
        if not cls.SUPABASE_URL:
            required_vars.append('SUPABASE_URL')
        if not cls.SUPABASE_ANON_KEY:
            required_vars.append('SUPABASE_ANON_KEY')

        if required_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(required_vars)}")

        # Warn about missing optional API keys
        missing_apis = []
        if not cls.GOLDAPI_KEY:
            missing_apis.append('GOLDAPI_KEY')
        if not cls.METALS_API_KEY:
            missing_apis.append('METALS_API_KEY')
        if not cls.ALPHA_VANTAGE_KEY:
            missing_apis.append('ALPHA_VANTAGE_KEY')

        if missing_apis:
            print(f"⚠️  Warning: Missing optional API keys: {', '.join(missing_apis)}")
            print("   Some price fetching services may not work.")

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}