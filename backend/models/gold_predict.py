try:
    from .live_price import LiveGoldPriceService
except ImportError:
    from live_price import LiveGoldPriceService
import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score, mean_squared_error

class GoldPricePredictor:
    def __init__(self):
        self.model = None
        self.scaler = MinMaxScaler()
        self.sequence_length = 30  # Use 30 days of history to predict next day
        self.gold_purities = {
            '24K': 1.0,
            '22K': 0.916,
            '18K': 0.750,
            '14K': 0.583
        }
        # Add live price service
        self.live_price_service = LiveGoldPriceService()
        # Get Alpha Vantage key
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
    
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
                usd_price = data['Close'].iloc[-1] / 31.1035  # GC=F per troy oz
                inr_rate = self.live_price_service.get_usd_to_inr_rate()
                return round(usd_price * inr_rate, 2)
        except:
            pass

        return None

    def fetch_gold_data_alpha_vantage(self, days=180):
        """Fetch historical gold data from Alpha Vantage"""
        if not self.alpha_vantage_key:
            return None
        
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GOLD_DAILY',
                'apikey': self.alpha_vantage_key
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                df = pd.DataFrame.from_dict(time_series, orient='index')
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                df['Price_Per_Gram'] = df['4. close'].astype(float) / 31.1035
                df = df.reset_index()
                df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Price_Per_Gram']
                df = df[['Date', 'Price_Per_Gram']]
                # Filter to last 'days' days
                cutoff_date = datetime.now() - timedelta(days=days)
                df = df[df['Date'] >= cutoff_date]
                return df
            else:
                print(f"Alpha Vantage error: {data.get('Note', 'Unknown error')}")
                return None
        except Exception as e:
            print(f"Error fetching from Alpha Vantage: {e}")
            return None

    def fetch_gold_data(self, days=180):
        """Fetch historical gold data"""
        # Try Alpha Vantage first
        df = self.fetch_gold_data_alpha_vantage(days)
        if df is not None and not df.empty:
            print("Fetched data from Alpha Vantage")
            
            # Save to data folder
            data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'gold_historical_data.csv')
            df.to_csv(data_path, index=False)
            print(f"Historical data saved to {data_path}")
            
            return df
        
        # Fallback to yfinance
        try:
            import yfinance as yf
            gold = yf.Ticker("GC=F")  # Gold futures
            df = gold.history(period="1y", interval="1d")  # Use 1y instead of 180d
            df = df.reset_index()
            df['Price_Per_Gram'] = df['Close'] / 31.1035  # GC=F is in USD per troy oz
            df['Date'] = pd.to_datetime(df['Date'])
            df = df[['Date', 'Price_Per_Gram']]
            
            if not df.empty:
                print("Fetched data from yfinance")
                
                # Save to data folder
                data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'gold_historical_data.csv')
                df.to_csv(data_path, index=False)
                print(f"Historical data saved to {data_path}")
                
                return df
            else:
                print("No data from yfinance")
        except Exception as e:
            print(f"Error fetching data: {e}")
        
        # Last resort: load from saved CSV
        try:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'gold_historical_data.csv')
            df = pd.read_csv(data_path)
            df['Date'] = pd.to_datetime(df['Date'])
            print("Loaded data from saved CSV")
            return df
        except Exception as e:
            print(f"Error loading saved data: {e}")
            return None

    def create_sequences(self, data, sequence_length):
        """Create sequences for LSTM training"""
        X, y = [], []
        for i in range(len(data) - sequence_length):
            X.append(data[i:i+sequence_length])
            y.append(data[i+sequence_length])
        return np.array(X), np.array(y)

    def build_lstm_model(self, input_shape):
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        model = Sequential([
            LSTM(50, activation='relu', input_shape=input_shape, return_sequences=True),
            Dropout(0.2),
            LSTM(50, activation='relu'),
            Dropout(0.2),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def build_gru_model(self, input_shape):
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import GRU, Dense, Dropout
        model = Sequential([
            GRU(50, activation='relu', input_shape=input_shape, return_sequences=True),
            Dropout(0.2),
            GRU(50, activation='relu'),
            Dropout(0.2),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def train_model(self, df):
        """Train and compare LSTM and GRU models, select the best one"""
        prices = df['Price_Per_Gram'].values.reshape(-1, 1)
        prices_scaled = self.scaler.fit_transform(prices)
        
        X, y = self.create_sequences(prices_scaled, self.sequence_length)
        
        # Split into train and validation
        train_size = int(0.8 * len(X))
        X_train, X_val = X[:train_size], X[train_size:]
        y_train, y_val = y[:train_size], y[train_size:]
        
        input_shape = (self.sequence_length, 1)
        
        # Train LSTM
        print(" Training LSTM model...")
        lstm_model = self.build_lstm_model(input_shape)
        lstm_model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=0)
        lstm_pred = lstm_model.predict(X_val, verbose=0).flatten()
        lstm_r2 = r2_score(y_val, lstm_pred)
        lstm_mse = mean_squared_error(y_val, lstm_pred)
        
        # Train GRU
        print(" Training GRU model...")
        gru_model = self.build_gru_model(input_shape)
        gru_model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=0)
        gru_pred = gru_model.predict(X_val, verbose=0).flatten()
        gru_r2 = r2_score(y_val, gru_pred)
        gru_mse = mean_squared_error(y_val, gru_pred)
        
        print(f"\nModel Comparison:")
        print(f"LSTM - R2: {lstm_r2:.4f}, MSE: {lstm_mse:.6f}")
        print(f"GRU  - R2: {gru_r2:.4f}, MSE: {gru_mse:.6f}")
        
        # Select best model (higher R2, lower MSE)
        if lstm_r2 > gru_r2 or (lstm_r2 == gru_r2 and lstm_mse < gru_mse):
            self.model = lstm_model
            print("Selected: LSTM")
        else:
            self.model = gru_model
            print("Selected: GRU")

    def predict_next_days(self, df, days=5):
        """Predict next days using LSTM"""
        prices = df['Price_Per_Gram'].values.reshape(-1, 1)
        prices_scaled = self.scaler.transform(prices)
        
        predictions = []
        current_sequence = prices_scaled[-self.sequence_length:].flatten()
        
        for _ in range(days):
            # Prepare input
            input_seq = current_sequence.reshape(1, self.sequence_length, 1)
            # Predict next value
            pred_scaled = self.model.predict(input_seq, verbose=0)[0][0]
            # Inverse transform
            pred = self.scaler.inverse_transform([[pred_scaled]])[0][0]
            predictions.append(pred)
            # Update sequence
            current_sequence = np.append(current_sequence[1:], pred_scaled)
        
        return predictions

    def convert_to_karat(self, price_24k, karat_type):
        """Convert 24K price to specified karat"""
        purity = self.gold_purities.get(karat_type, 1.0)
        return price_24k * purity

    def get_predictions(self, karat_type='24K', use_live_price=True):
        """
        Get predictions starting from LIVE price
        """
        try:
            print(f"\n{'='*50}")
            print(f"Gold Price Prediction - {karat_type}")
            print(f"{'='*50}\n")

            # Get LIVE current price
            if use_live_price:
                print(" Fetching live gold price...")
                today_price_24k = self.get_current_live_price()

                if today_price_24k:
                    print(f" Live price: ₹{today_price_24k:.2f}/gram (24K)")
                else:
                    print("  Could not fetch live price, using historical data...")
                    df = self.fetch_gold_data(days=180)
                    if df is None or df.empty:
                        print("  Failed to fetch historical data for live price fallback")
                        return None
                    today_price_24k = df['Price_Per_Gram'].iloc[-1]
            else:
                # Use historical data
                df = self.fetch_gold_data(days=180)
                if df is None or df.empty:
                    print("  Failed to fetch historical data")
                    return None
                today_price_24k = df['Price_Per_Gram'].iloc[-1]

            # Train model on historical data
            df = self.fetch_gold_data(days=180)
            if df is None:
                print(" Failed to fetch historical data for training")
                return None
            if len(df) < self.sequence_length + 10:
                print(" Not enough data for training")
                return None
            self.train_model(df)

            # Make predictions
            print(" Generating predictions...")
            predictions_24k = self.predict_next_days(df, days=5)

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

            # Save predictions to data folder
            pred_dates = [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 6)]
            pred_df = pd.DataFrame({
                'Date': pred_dates,
                'Predicted_Price_24K': predictions
            })
            pred_path = os.path.join(os.path.dirname(__file__), '..', 'data', f'gold_predictions_{karat_type}_{datetime.now().strftime("%Y%m%d")}.csv')
            pred_df.to_csv(pred_path, index=False)
            print(f"Predictions saved to {pred_path}")

            return {
                'karat_type': karat_type,
                'today_price': round(today_price, 2),
                'is_live': use_live_price,
                'predictions': [round(p, 2) for p in predictions],
                'source': 'Live Market Data' if use_live_price else 'Historical Data'
            }
        except Exception as e:
            print(f"Error in get_predictions: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


# Test the predictor
if __name__ == "__main__":
    predictor = GoldPricePredictor()
    result = predictor.get_predictions()
    if result:
        print(" Successfully generated gold price predictions!")
    else:
        print(" Failed to generate predictions.")
