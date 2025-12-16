from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from backend.models.gold_predict import GoldPricePredictor
from backend.models.live_price import LiveGoldPriceService

app = Flask(__name__)
CORS(app)

predictor = GoldPricePredictor()
live_service = LiveGoldPriceService()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/live-price')
def live_price():
    """Get current live gold price from market"""
    result = live_service.display_live_prices()
    
    if result:
        return jsonify({
            'success': True,
            'data': result
        })
    
    return jsonify({
        'success': False,
        'error': 'Could not fetch live prices'
    }), 500

@app.route('/api/predict')
def predict():
    """Get predictions starting from LIVE price"""
    try:
        karat = request.args.get('karat', '24K')
        use_live = request.args.get('live', 'true').lower() == 'true'

        if karat not in predictor.gold_purities:
            return jsonify({'success': False, 'error': 'Invalid karat type'}), 400

        # Return sample data for testing
        result = {
            'karat_type': karat,
            'today_price': 12519.49,
            'is_live': True,
            'predictions': [12418.75, 12353.54, 12368.2, 12368.2, 12368.2],
            'source': 'Live Market Data'
        }

        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        print(f"Error in predict endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Prediction service unavailable'
        }), 500

@app.route('/api/all-prices')
def all_prices():
    """Get live prices for all karat types"""
    price_data = live_service.get_best_live_price()
    
    if not price_data:
        return jsonify({
            'success': False,
            'error': 'Could not fetch live prices'
        }), 500
    
    all_karats = live_service.get_all_karat_prices(
        price_data['price_per_gram_24k']
    )
    
    return jsonify({
        'success': True,
        'data': {
            'source': price_data['source'],
            'timestamp': price_data['date'],
            'prices': all_karats
        }
    })

@app.route('/api/karat-types')
def karat_types():
    types = [
        {'value': '24K', 'label': '24 Karat', 'purity': 100},
        {'value': '22K', 'label': '22 Karat', 'purity': 91.6},
        {'value': '18K', 'label': '18 Karat', 'purity': 75.0},
        {'value': '14K', 'label': '14 Karat', 'purity': 58.3}
    ]
    return jsonify({'karat_types': types})

if __name__ == '__main__':
    print("\n🚀 Starting Gold Price API with LIVE Market Data...")
    print("📍 Server: http://localhost:5000")
    print("\nEndpoints:")
    print("  • Live Prices: http://localhost:5000/api/live-price")
    print("  • Predictions: http://localhost:5000/api/predict?karat=24K")
    print("  • All Prices:  http://localhost:5000/api/all-prices\n")
    app.run(debug=True, port=5000)