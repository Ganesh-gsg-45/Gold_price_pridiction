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
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': 'Could not fetch prices'}), 500

@api_bp.route('/predict')
@handle_errors
def predict():
    """Get predictions"""
    karat = request.args.get('karat', '24K')
    result = predictor.get_predictions(karat, use_live_price=True)
    return jsonify({'success': True, 'data': result})

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

@api_bp.route('/karat-types')
def karat_types():
    """Get available karat types"""
    types = [
        {'value': '24K', 'label': '24 Karat', 'purity': 100},
        {'value': '22K', 'label': '22 Karat', 'purity': 91.6},
        {'value': '18K', 'label': '18 Karat', 'purity': 75.0},
        {'value': '14K', 'label': '14 Karat', 'purity': 58.3}
    ]
    return jsonify({'karat_types': types})
@api_bp.route('/calculator')
@handle_errors
def calculator():
    """
    Gold price calculator endpoint
    Calculate price for specific weight and karat
    """
    karat = request.args.get('karat', '24K')
    weight = request.args.get('weight', type=float, default=1.0)
    
    if karat not in predictor.gold_purities:
        return jsonify({'success': False, 'error': 'Invalid karat type'}), 400
    
    if weight <= 0:
        return jsonify({'success': False, 'error': 'Weight must be positive'}), 400
    
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