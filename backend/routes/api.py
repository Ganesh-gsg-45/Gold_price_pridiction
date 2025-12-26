"""
API Routes Blueprint
"""

import sys
import os
# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from flask import Blueprint, jsonify, request
from backend.models.gold_predict import GoldPricePredictor
from backend.models.live_price import LiveGoldPriceService
from backend.utils.helper import handle_errors
from supabase_client import save_today_price, save_predictions

api_bp = Blueprint('api', __name__)

# Initialize services
predictor = GoldPricePredictor()
price_service = LiveGoldPriceService()

@api_bp.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'healthy'})

@api_bp.route('/live-price')
@handle_errors
def live_price():
    """Get live prices"""
    result = price_service.display_live_prices()
    if result:
        # Try to save historical prices to database (optional)
        try:
            for karat, data in result['all_karats'].items():
                save_today_price(karat, data['price_per_gram'])
        except Exception as e:
            logger.warning(f"Could not save to database: {e}")
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': 'Could not fetch live prices. Using sample data instead.'}), 200

@api_bp.route('/predict')
def predict():
    """Get predictions"""
    try:
        karat = request.args.get('karat', '24K')
        result = predictor.get_predictions(karat, use_live_price=True)
        if result is None:
            return jsonify({'success': False, 'error': 'Failed to generate predictions'}), 500
        # Try to save predictions to database (optional)
        try:
            save_predictions(karat, result['predictions'])
        except Exception as e:
            logger.warning(f"Could not save predictions to database: {e}")
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        print(f"Error in predict endpoint: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error', 'details': str(e)}), 500

@api_bp.route('/all-prices')
@handle_errors
def all_prices():
    """Get all karat prices"""
    price_data = price_service.get_best_live_price()
    if not price_data:
        return jsonify({'success': False, 'error': 'Could not fetch prices'}), 500

    # Get INR conversion rate
    inr_rate = price_service.get_usd_to_inr_rate()

    # Convert 24K price to INR
    price_per_gram_24k_inr = price_data['price_per_gram_24k'] * inr_rate

    # Get all karat prices in INR
    all_karats_inr = price_service.get_all_karat_prices(price_per_gram_24k_inr)

    return jsonify({
        'success': True,
        'data': {
            'source': price_data['source'],
            'timestamp': price_data['date'],
            'prices': all_karats_inr
        }
    })

@api_bp.route('/historical-prices')
@handle_errors
def historical_prices():
    """Get historical prices for the last 6 days"""
    try:
        import pandas as pd
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'gold_historical_data.csv')
        df = pd.read_csv(data_path)
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        
        # Get last 5 days (excluding today), sorted descending (most recent first)
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        df = df[df['Date'] != today].sort_values('Date', ascending=False).head(5)
        
        # Convert to INR (assuming the prices are in USD, convert using current rate)
        inr_rate = price_service.get_usd_to_inr_rate()
        df['Price_Per_Gram_INR'] = df['Price_Per_Gram'] * inr_rate
        
        # Format for frontend
        historical_data = []
        for _, row in df.iterrows():
            historical_data.append({
                'date': row['Date'].strftime('%Y-%m-%d'),
                'price_usd': round(row['Price_Per_Gram'], 2),
                'price_inr': round(row['Price_Per_Gram_INR'], 2)
            })
        
        return jsonify({
            'success': True,
            'data': historical_data
        })
    except Exception as e:
        print(f"Error loading historical data: {e}")
        return jsonify({'success': False, 'error': 'Could not load historical data'}), 500
@api_bp.route('/calculator')
@handle_errors
def calculator():
    """
    Gold price calculator endpoint
    Calculate price for specific weight and karat
    """
    karat = request.args.get('karat', '24K')
    weight = request.args.get('weight', type=float, default=1.0)

    # Input validation
    if karat not in predictor.gold_purities:
        return jsonify({'success': False, 'error': f'Invalid karat type. Must be one of: {", ".join(predictor.gold_purities.keys())}'}), 400

    if weight <= 0 or weight > 10000:  # Reasonable upper limit
        return jsonify({'success': False, 'error': 'Weight must be positive and less than 10,000 grams'}), 400
    
    # Get current price
    price_data = price_service.get_best_live_price()
    if not price_data:
        return jsonify({'success': False, 'error': 'Could not fetch prices'}), 500
    
    # Get INR conversion
    inr_rate = price_service.get_usd_to_inr_rate()
    price_per_gram_24k = price_data['price_per_gram_24k'] * inr_rate
    
    # Convert to selected karat
    purity = predictor.gold_purities[karat]
    price_per_gram = price_per_gram_24k * purity
    total_price = price_per_gram * weight
    
    return jsonify({
        'success': True,
        'data': {
            'karat': karat,
            'weight': weight,
            'price_per_gram': round(price_per_gram, 2),
            'total_price': round(total_price, 2),
            'purity': f"{purity * 100}%",
            'source': price_data['source'],
            'timestamp': price_data['date']
        }
    })