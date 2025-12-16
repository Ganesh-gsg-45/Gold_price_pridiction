"""
Application Configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('API_SECRET_KEY', 'dev-secret-key')
    DEBUG = False
    TESTING = False
    
    # API Keys
    GOLDAPI_KEY = os.getenv('GOLDAPI_KEY')
    METALS_API_KEY = os.getenv('METALS_API_KEY')
    ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')
    
    # Gold purities
    GOLD_PURITIES = {
        '24K': 1.0,
        '22K': 0.916,
        '18K': 0.750,
        '14K': 0.583
    }

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