from .live_price import LiveGoldPriceService
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor

class GoldPricePredictor:
    def __init__(self):
        self.model = None
        self.scaler_X = MinMaxScaler()
        self.scaler_y = MinMaxScaler()
        self.gold_purities = {
            '24K': 1.0,
            '22K': 0.916,
            '18K': 0.750,
            '14K': 0.583
        }
        # Add live price service
        self.live_price_service = LiveGoldPriceService()
    
    def get_current_live_price(self):
        """Get current live gold price in INR"""
        price_data = self.live_price_service.get_best_live_price()

        if price_data:
            # Get INR price
            inr_rate = self.live_price_service.get_usd_to_inr_rate()
            usd_price = price_data['price_per_gram_24k']
            inr_price = usd_price * inr_rate
            return round(inr_price, 2)

        # Fallback to yfinance if APIs fail
        try:
            import yfinance as yf
            gold = yf.Ticker("GC=F")
            data = gold.history(period="1d", interval="1m")
            if not data.empty:
                usd_price = (data['Close'].iloc[-1]) / 31.1035
                inr_rate = self.live_price_service.get_usd_to_inr_rate()
                return round(usd_price * inr_rate, 2)
        except:
            pass

        return None

    def fetch_gold_data(self, days=180):
        """Fetch historical gold data"""
        try:
            import yfinance as yf
            gold = yf.Ticker("GC=F")
            df = gold.history(period=f"{days}d", interval="1d")
            df = df.reset_index()
            df['Price_Per_Gram'] = df['Close'] / 31.1035
            df['Date'] = pd.to_datetime(df['Date'])
            df = df[['Date', 'Price_Per_Gram']]
            return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

    def create_features(self, df):
        """Create features for ML model"""
        df = df.copy()
        df['lag_1'] = df['Price_Per_Gram'].shift(1)
        df['lag_7'] = df['Price_Per_Gram'].shift(7)
        df['rolling_mean_7'] = df['Price_Per_Gram'].rolling(window=7).mean()
        df['rolling_std_7'] = df['Price_Per_Gram'].rolling(window=7).std()
        return df

    def train_model(self, df_features):
        """Train the ML model"""
        df_features = df_features.dropna()
        X = df_features[['lag_1', 'lag_7', 'rolling_mean_7', 'rolling_std_7']]
        y = df_features['Price_Per_Gram']
        X_scaled = self.scaler_X.fit_transform(X)
        y_scaled = self.scaler_y.fit_transform(y.values.reshape(-1, 1)).ravel()
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y_scaled)

    def predict_next_days(self, df_features, days=5):
        """Predict next days"""
        predictions = []
        last_row = df_features.iloc[-1]
        current_features = last_row[['lag_1', 'lag_7', 'rolling_mean_7', 'rolling_std_7']].values.reshape(1, -1)

        for _ in range(days):
            current_features_scaled = self.scaler_X.transform(current_features)
            pred_scaled = self.model.predict(current_features_scaled)[0]
            pred = self.scaler_y.inverse_transform([[pred_scaled]])[0][0]
            predictions.append(pred)
            # Update features for next prediction
            current_features = np.array([pred, last_row['lag_1'], last_row['rolling_mean_7'], last_row['rolling_std_7']]).reshape(1, -1)

        return predictions

    def convert_to_karat(self, price_24k, karat_type):
        """Convert 24K price to specified karat"""
        purity = self.gold_purities.get(karat_type, 1.0)
        return price_24k * purity

    def get_predictions(self, karat_type='24K', use_live_price=True):
        """
        Get predictions starting from LIVE price
        """
        print(f"\n{'='*50}")
        print(f"Gold Price Prediction - {karat_type}")
        print(f"{'='*50}\n")
        
        # Get LIVE current price
        if use_live_price:
            print("📡 Fetching live gold price...")
            today_price_24k = self.get_current_live_price()
            
            if today_price_24k:
                print(f"✅ Live price: ₹{today_price_24k:.2f}/gram (24K)")
            else:
                print("⚠️  Could not fetch live price, using historical data...")
                df = self.fetch_gold_data(days=180)
                today_price_24k = df['Price_Per_Gram'].iloc[-1]
        else:
            # Use historical data
            df = self.fetch_gold_data(days=180)
            today_price_24k = df['Price_Per_Gram'].iloc[-1]
        
        # Train model on historical data
        df = self.fetch_gold_data(days=180)
        df_features = self.create_features(df)
        df_features = df_features.dropna()
        self.train_model(df_features)
        
        # Make predictions
        print("🔮 Generating predictions...")
        predictions_24k = self.predict_next_days(df_features, days=5)
        
        # Adjust predictions based on live price
        # Scale predictions to start from current live price
        if use_live_price and today_price_24k:
            historical_last = df['Price_Per_Gram'].iloc[-1]
            # Convert INR live price back to USD for adjustment calculation
            inr_rate = self.live_price_service.get_usd_to_inr_rate()
            live_price_usd = today_price_24k / inr_rate
            adjustment = live_price_usd - historical_last
            predictions_24k = [p + adjustment for p in predictions_24k]
            predictions_24k = [p * inr_rate for p in predictions_24k]
        
        # Convert to selected karat
        today_price = self.convert_to_karat(today_price_24k, karat_type)
        predictions = [self.convert_to_karat(p, karat_type) 
                      for p in predictions_24k]
        
        # Display results
        print(f"\n TODAY ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        print(f"   LIVE Price: ₹{today_price:.2f}/gram\n")
        
        print(" NEXT 5 DAYS PREDICTIONS:")
        for i, pred in enumerate(predictions, 1):
            date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            change = pred - today_price
            change_pct = (change / today_price) * 100
            arrow = "↑" if change > 0 else "↓"
            
            print(f"   Day {i} ({date}): ₹{pred:.2f} {arrow} {change_pct:+.2f}%")
        
        print(f"\n{'='*50}\n")
        
        return {
            'karat_type': karat_type,
            'today_price': round(today_price, 2),
            'is_live': use_live_price,
            'predictions': [round(p, 2) for p in predictions],
            'source': 'Live Market Data' if use_live_price else 'Historical Data'
        }


# Test the predictor
if __name__ == "__main__":
    predictor = GoldPricePredictor()
    result = predictor.get_predictions()
    if result:
        print(" Successfully generated gold price predictions!")
    else:
        print(" Failed to generate predictions.")
def get_predictions(self, karat_type='24K'):
    print(f"\n{'='*50}")
    print(f"Gold Price Prediction - {karat_type}")
    print(f"{'='*50}\n")

    df = self.fetch_gold_data(days=180)
    df_features = self.create_features(df)
    self.train_model(df_features)

    predictions_24k = self.predict_next_days(df_features, days=5)
    today_price_24k = df['Price_Per_Gram'].iloc[-1]

    today_price = self.convert_to_karat(today_price_24k, karat_type)
    predictions = [self.convert_to_karat(p, karat_type) for p in predictions_24k]

    self.save_today_price(karat_type, today_price)
    self.save_predictions(karat_type, predictions)

    print(f"\n TODAY ({datetime.now().strftime('%Y-%m-%d')})")
    print(f"   Price: ${today_price:.2f}/gram\n")

    print(" NEXT 5 DAYS:")
    for i, pred in enumerate(predictions, 1):
        date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
        change = pred - today_price
        change_pct = (change / today_price) * 100
        arrow = "↑" if change > 0 else "↓"
        print(f"   Day {i} ({date}): ${pred:.2f} {arrow} {change_pct:+.2f}%")

    print(f"\n{'='*50}\n")

    return {
        'karat_type': karat_type,
        'today_price': round(today_price, 2),
        'predictions': [round(p, 2) for p in predictions]
    }
