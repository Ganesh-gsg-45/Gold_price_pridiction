"""
Complete Test Script
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print(" Testing Gold Price Predictor")
print("="*60)

# Test 1: Imports
print("\n1. Testing Imports...")
try:
    from models.gold_predict import GoldPricePredictor
    print("   GoldPricePredictor imported")
except Exception as e:
    print(f"    Error: {e}")
    sys.exit(1)

try:
    from models.live_price import LiveGoldPriceService
    print("    LiveGoldPriceService imported")
except Exception as e:
    print(f"    Error: {e}")
    sys.exit(1)

try:
    from config import config
    print("    Config imported")
except Exception as e:
    print(f"    Error: {e}")
    sys.exit(1)

# Test 2: Live Price Service
print("\n2. Testing Live Price Service...")
try:
    service = LiveGoldPriceService()
    price = service.get_best_live_price()
    if price:
        print(f"    Live price: ${price['price_per_gram_24k']}/gram")
        print(f"    Source: {price['source']}")
    else:
        print("     Could not fetch live price")
except Exception as e:
    print(f"    Error: {e}")

# Test 3: Predictor
print("\n3. Testing Predictor...")
try:
    predictor = GoldPricePredictor()
    print("   Predictor initialized")
    
    result = predictor.get_predictions('24K', use_live_price=True)
    print(f"    Today's price: ₹{result['today_price']}")
    print(f"    Predictions: {len(result['predictions'])} days")
    print(f"    Sample prediction: ₹{result['predictions'][0]}")
except Exception as e:
    print(f"    Error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Flask App
print("\n4. Testing Flask App...")
try:
    from app import create_app
    app = create_app('development')
    print("    Flask app created")
    
    with app.test_client() as client:
        # Test health endpoint
        response = client.get('/api/health')
        print(f"   Health check: {response.status_code}")
        
        # Test karat-types endpoint
        response = client.get('/api/karat-types')
        if response.status_code == 200:
            print(f"    Karat types: {response.status_code}")
        else:
            print(f"     Karat types: {response.status_code}")
            
except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Testing Complete!")
print("="*60 + "\n")
print("Next steps:")
print("1. Run: python app.py")
print("2. Visit: http://localhost:5000")
print("3. Test predictions in the UI")