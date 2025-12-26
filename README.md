#  Gold Price Predictor

AI-powered gold price prediction system with real-time market data, machine learning forecasts, and user authentication.

##  Features

-  **Real-time Prices** - Live gold prices in INR from multiple sources with 5-minute caching
-  **ML Predictions** - 5-day price forecasts using Random Forest regression
- **Multiple Types** - Support for 24K, 22K, 18K, and 14K gold with automatic purity calculations
-  **User Authentication** - Secure login/registration with Supabase backend
-  **Beautiful UI** - Modern, responsive web interface with login and calculator pages
-  **Price Calculator** - Calculate gold prices for specific weights and karats
-  **Auto-fallback** - Multiple API sources for reliability (GoldAPI, Metals-API, Yahoo Finance)
-  **Security** - Input validation, error handling, and secure configuration
-  **Logging** - Proper logging system instead of console prints

##  Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation
```bash
# Clone repository
git clone <your-repo-url>
cd gold-price-prediction

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

### Configuration

1. **Create `.env` file** in `backend/` folder:
```bash
# API Keys (optional - works without them!)
GOLDAPI_KEY=your_goldapi_key_here
METALS_API_KEY=your_metals_api_key_here
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here

# App Settings
API_SECRET_KEY=your-secret-key-here
```

2. **Get API Keys** (Optional):
   - **GoldAPI**: https://www.goldapi.io/ (50 requests/month free)
   - **Metals-API**: https://metals-api.com/ (100 requests/month free)
   - **Alpha Vantage**: https://www.alphavantage.co/ (25 requests/day free)

> **Note:** Yahoo Finance works without any API key!

### Run Application
```bash
# Make sure you're in backend folder
cd backend

# Run the server
python app.py
```

Visit: **http://localhost:5000**

##  Project Structure
```
backend/
├── app.py                  # Main Flask application
├── config.py              # Configuration settings
├── models/
│   ├── gold_predict.py    # ML prediction model
│   └── live_price.py      # Price fetching service
├── routes/
│   ├── __init__.py
│   └── api.py            # API endpoints
├── utils/
│   ├── __init__.py
│   └── helper.py         # Helper functions
├── static/
│   ├── style.css         # Styles
│   └── script.js         # Frontend JS
├── templates/
│   └── index.html        # Main page
├── .env                  # Environment variables
└── requirements.txt      # Dependencies
```

##  API Endpoints

### Health Check
```http
GET /api/health
```

### Get Live Prices
```http
GET /api/live-price
```
Returns current prices for all gold types in INR.

### Get Predictions
```http
GET /api/predict?karat=24K
```
Parameters:
- `karat`: Gold type (24K, 22K, 18K, 14K)

Returns today's price and 5-day predictions.

### Get All Prices
```http
GET /api/all-prices
```
Returns all karat types with current prices.

### Get Karat Types
```http
GET /api/karat-types
```
Returns available gold types and purities.

##  Testing
```bash
# Test imports
python -c "from models.gold_predict import GoldPricePredictor; print(' Imports working')"

# Test predictor
cd backend/models
python gold_predict.py

# Test live prices
python live_price.py

# Test API health
curl http://localhost:5000/api/health
```

## Tech Stack

- **Backend:** Flask 2.3.3
- **ML:** scikit-learn, Random Forest
- **Data:** yfinance, pandas, numpy
- **APIs:** GoldAPI, Metals-API, Yahoo Finance
- **Frontend:** HTML5, CSS3, JavaScript

##  How It Works

1. **Data Collection**: Fetches historical gold prices from Yahoo Finance
2. **Feature Engineering**: Creates technical indicators (MA, RSI, volatility)
3. **Model Training**: Random Forest regression on historical data
4. **Live Pricing**: Gets current prices from multiple APIs
5. **Prediction**: Forecasts next 5 days starting from live price
6. **Currency Conversion**: Converts USD to INR automatically

##  Security

- Environment variables for sensitive data
- CORS enabled for frontend
- Error handling on all endpoints
- Input validation for API parameters

##  Future Enhancements

- [ ] User authentication
- [ ] Price alert notifications
- [ ] Historical charts
- [ ] Email/SMS alerts
- [ ] Mobile app
- [ ] Database storage
- [ ] More ML models (LSTM, Prophet)

##  Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

##  Disclaimer

This application is for informational and educational purposes only. Predictions should not be considered as financial advice. Always consult with qualified financial advisors before making investment decisions.

##  License

MIT License - see LICENSE file

##  Author

Your Name - your.email@example.com

##  Acknowledgments

- Data from Yahoo Finance, GoldAPI, Metals-API
- Built with Flask and scikit-learn
- UI inspired by modern fintech applications

---

**Made with  and Python**