import requests
import os
import logging
from dotenv import load_dotenv
from datetime import datetime

# Set up logger
logger = logging.getLogger(__name__)

# Load environment variables from backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class LiveGoldPriceService:
    def __init__(self):
        # Get API key from .env
        self.goldapi_key = os.getenv('GOLDAPI_KEY')
        self.metals_api_key = os.getenv('METALS_API_KEY')
        self.alphavantage_api_key = os.getenv('ALPHAVANTAGE_KEY')

        self.gold_purities = {
            '24K': 1.0,
            '22K': 0.916,
            '18K': 0.750,
            '14K': 0.583
        }

        # Cache for currency conversion
        self.usd_to_inr_rate = None
        self.rate_timestamp = None

        # Cache for price data
        self.price_cache = None
        self.price_cache_timestamp = None
        self.cache_duration = 300  # 5 minutes in seconds

    def get_usd_to_inr_rate(self):
        """
        Get USD to INR conversion rate
        Uses free exchangerate API
        """
        # Check if we have a cached rate less than 1 hour old
        if self.usd_to_inr_rate and self.rate_timestamp:
            if (datetime.now() - self.rate_timestamp).seconds < 3600:  # 1 hour
                return self.usd_to_inr_rate

        try:
            # Using exchangerate-api.com (free, no API key needed)
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200 and 'rates' in data:
                self.usd_to_inr_rate = data['rates'].get('INR', 83.0)  # Fallback to ~83 INR/USD
                self.rate_timestamp = datetime.now()
                logger.info(f"USD to INR rate: {self.usd_to_inr_rate}")
                return self.usd_to_inr_rate
            else:
                logger.warning("Could not fetch currency conversion rate")
                return 83.0  # Fallback rate

        except Exception as e:
            logger.error(f"Error fetching currency rate: {e}")
            return 83.0  # Fallback rate
    
    def get_live_gold_price_goldapi(self):
        """
        Get live gold price from GoldAPI.io
        Most accurate - shows actual market rates
        """
        if not self.goldapi_key:
            logger.warning("No GoldAPI key found. Get one at https://www.goldapi.io/")
            return None
        
        url = "https://www.goldapi.io/api/XAU/USD"
        headers = {
            "x-access-token": self.goldapi_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if response.status_code == 200:
                # GoldAPI returns price per troy ounce
                price_per_oz = data['price']
                # Convert to price per gram (1 troy oz = 31.1035 grams)
                price_per_gram = price_per_oz / 31.1035
                
                return {
                    'source': 'GoldAPI.io',
                    'price_per_gram_24k': round(price_per_gram, 2),
                    'price_per_oz': round(price_per_oz, 2),
                    'currency': 'USD',
                    'timestamp': data['timestamp'],
                    'date': datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                    'raw_data': data
                }
            else:
                logger.error(f"GoldAPI Error: {data.get('message', 'Unknown error')}")
                return None

        except Exception as e:
            logger.error(f"Error fetching from GoldAPI: {e}")
            return None

    def get_live_gold_price_metals_api(self):
        """
        Get live gold price from Metals-API.com
        Alternative source - also very accurate
        """
        if not self.metals_api_key:
            logger.warning("No Metals-API key found. Get one at https://metals-api.com/")
            return None
        
        url = f"https://metals-api.com/api/latest"
        params = {
            'access_key': self.metals_api_key,
            'base': 'XAU',  # Gold
            'symbols': 'USD'
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('success'):
                # Metals-API returns USD per troy ounce of gold
                rate = data['rates']['USD']
                price_per_oz = 1 / rate  # Invert to get price of gold in USD
                price_per_gram = price_per_oz / 31.1035
                
                return {
                    'source': 'Metals-API',
                    'price_per_gram_24k': round(price_per_gram, 2),
                    'price_per_oz': round(price_per_oz, 2),
                    'currency': 'USD',
                    'timestamp': data['timestamp'],
                    'date': datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                    'raw_data': data
                }
            else:
                logger.error(f"Metals-API Error: {data.get('error', {}).get('info', 'Unknown error')}")
                return None

        except Exception as e:
            logger.error(f"Error fetching from Metals-API: {e}")
            return None

    def get_live_gold_price_yahoo(self):
        """
        Get live gold price from Yahoo Finance (FREE - No API key needed)
        Good backup option
        """
        try:
            import yfinance as yf

            # GC=F is Gold Futures
            # GLD is Gold ETF (more stable)
            gold = yf.Ticker("GC=F")

            # Get current price
            data = gold.history(period="1d", interval="1m")

            if not data.empty:
                latest_price = data['Close'].iloc[-1]
                # Gold futures are in USD per troy ounce
                price_per_gram = latest_price / 31.1035

                return {
                    'source': 'Yahoo Finance',
                    'price_per_gram_24k': round(price_per_gram, 2),
                    'price_per_oz': round(latest_price, 2),
                    'currency': 'USD',
                    'timestamp': int(data.index[-1].timestamp()),
                    'date': data.index[-1].strftime('%Y-%m-%d %H:%M:%S'),
                    'raw_data': data.iloc[-1].to_dict()
                }

            return None

        except Exception as e:
            logger.error(f"Error fetching from Yahoo: {e}")
            return None

    def get_live_gold_price_alphavantage(self):
        """
        Get live gold price from Alpha Vantage API
        Uses GLD (Gold ETF) as a proxy for gold prices
        Good alternative source
        """
        if not self.alphavantage_api_key:
            logger.warning("No Alpha Vantage API key found. Get one at https://www.alphavantage.co/")
            return None

        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': 'GLD',  # SPDR Gold Shares ETF
            'apikey': self.alphavantage_api_key
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if response.status_code == 200 and 'Global Quote' in data:
                quote = data['Global Quote']
                price_per_share = float(quote['05. price'])

                # GLD ETF holds gold, each share represents ~0.1 troy ounces of gold
                # So price per share / 0.1 = price per troy ounce
                price_per_oz = price_per_share / 0.1
                price_per_gram = price_per_oz / 31.1035

                return {
                    'source': 'Alpha Vantage (GLD ETF)',
                    'price_per_gram_24k': round(price_per_gram, 2),
                    'price_per_oz': round(price_per_oz, 2),
                    'currency': 'USD',
                    'timestamp': int(datetime.now().timestamp()),
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'raw_data': data
                }
            else:
                logger.error(f"Alpha Vantage Error: {data.get('Error Message', 'Unknown error')}")
                return None

        except Exception as e:
            logger.error(f"Error fetching from Alpha Vantage: {e}")
            return None

    def get_best_live_price(self):
        """
        Try multiple sources and return the best available price
        Priority: GoldAPI > Metals-API > Yahoo Finance > Alpha Vantage > Sample Data
        Uses caching to avoid excessive API calls
        """
        # Check cache first
        if self.price_cache and self.price_cache_timestamp:
            if (datetime.now() - self.price_cache_timestamp).seconds < self.cache_duration:
                logger.info("Using cached price data")
                return self.price_cache

        logger.info("Fetching live gold prices...")

        # Try GoldAPI first (most accurate)
        price_data = self.get_live_gold_price_goldapi()
        if price_data:
            logger.info(f"Got price from {price_data['source']}")
            self.price_cache = price_data
            self.price_cache_timestamp = datetime.now()
            return price_data

        # Try Metals-API
        price_data = self.get_live_gold_price_metals_api()
        if price_data:
            logger.info(f"Got price from {price_data['source']}")
            self.price_cache = price_data
            self.price_cache_timestamp = datetime.now()
            return price_data

        # Try Yahoo Finance (free backup)
        price_data = self.get_live_gold_price_yahoo()
        if price_data:
            logger.info(f"Got price from {price_data['source']}")
            self.price_cache = price_data
            self.price_cache_timestamp = datetime.now()
            return price_data

        # Try Alpha Vantage (additional backup)
        price_data = self.get_live_gold_price_alphavantage()
        if price_data:
            logger.info(f"Got price from {price_data['source']}")
            self.price_cache = price_data
            self.price_cache_timestamp = datetime.now()
            return price_data

        # Fallback to sample data
        logger.warning("All APIs failed, using sample data")
        price_data = self.get_sample_live_price()
        self.price_cache = price_data
        self.price_cache_timestamp = datetime.now()
        return price_data
    
    def get_sample_live_price(self):
        """
        Return sample live price data when APIs are unavailable
        """
        # Sample price around current market rates (as of 2024)
        sample_price_per_gram = 86.5  # USD per gram 24K
        
        return {
            'source': 'Sample Data (APIs Unavailable)',
            'price_per_gram_24k': sample_price_per_gram,
            'price_per_oz': round(sample_price_per_gram * 31.1035, 2),
            'currency': 'USD',
            'timestamp': int(datetime.now().timestamp()),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'raw_data': {'note': 'Sample data used because APIs are unavailable'}
        }
    
    def get_all_karat_prices(self, base_price_24k):
        """
        Convert 24K price to all karat types
        """
        prices = {}
        
        for karat, purity in self.gold_purities.items():
            price = base_price_24k * purity
            prices[karat] = {
                'price_per_gram': round(price, 2),
                'price_per_10g': round(price * 10, 2),
                'price_per_oz': round(price * 31.1035, 2),
                'purity': f"{purity * 100}%"
            }
        
        return prices
    
    def display_live_prices(self):
        """
        Display live prices in a nice format
        """
        price_data = self.get_best_live_price()

        if not price_data:
            return None

        # Get conversion rate
        inr_rate = self.get_usd_to_inr_rate()

        # Convert prices to INR
        price_per_gram_24k_inr = round(price_data['price_per_gram_24k'] * inr_rate, 2)
        price_per_oz_inr = round(price_data['price_per_oz'] * inr_rate, 2)

        logger.info(f"LIVE GOLD PRICES - {price_data['date']}")
        logger.info(f"Source: {price_data['source']}")
        logger.info(f"Currency: INR (₹) | USD Rate: ₹{inr_rate}/$")
        logger.info(f"24K Gold (Pure): ₹{price_per_gram_24k_inr}/gram")
        logger.info(f"             or: ₹{price_per_oz_inr}/troy oz")

        # Get all karat prices in INR
        all_prices_usd = self.get_all_karat_prices(price_data['price_per_gram_24k'])
        all_prices_inr = {}

        for karat, data in all_prices_usd.items():
            all_prices_inr[karat] = {
                'price_per_gram': round(data['price_per_gram'] * inr_rate, 2),
                'price_per_10g': round(data['price_per_10g'] * inr_rate, 2),
                'price_per_oz': round(data['price_per_oz'] * inr_rate, 2),
                'purity': data['purity']
            }

        logger.info("All Karat Types:")

        for karat, data in all_prices_inr.items():
            logger.info(f"{karat:4s} ({data['purity']:6s}): ₹{data['price_per_gram']:7.2f}/gram  "
                  f"₹{data['price_per_10g']:8.2f}/10g  ₹{data['price_per_oz']:9.2f}/oz")

        # Update price_data with INR prices
        price_data_inr = price_data.copy()
        price_data_inr['price_per_gram_24k'] = price_per_gram_24k_inr
        price_data_inr['price_per_oz'] = price_per_oz_inr
        price_data_inr['currency'] = 'INR'

        return {
            'base_data': price_data_inr,
            'all_karats': all_prices_inr,
            'usd_prices': {
                'base_data': price_data,
                'all_karats': all_prices_usd
            },
            'conversion_rate': inr_rate
        }


# Test the service
if __name__ == "__main__":
    service = LiveGoldPriceService()
    result = service.display_live_prices()

    if result:
        logger.info("Successfully fetched live gold prices!")
    else:
        logger.error("Failed to fetch live prices. Check your API keys.")
