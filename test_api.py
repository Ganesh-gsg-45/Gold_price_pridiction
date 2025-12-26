import requests

print('=== Testing API Endpoints ===')

# Test health
try:
    r = requests.get('http://localhost:5000/api/health')
    print(f'Health: {r.status_code} - {r.json()}')
except Exception as e:
    print(f'Health check failed: {e}')

# Test live price
try:
    r = requests.get('http://localhost:5000/api/live-price')
    print(f'Live Price: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'Success: {data["success"]}, Source: {data["data"]["base_data"]["source"]}')
except Exception as e:
    print(f'Live price check failed: {e}')

# Test historical prices
try:
    r = requests.get('http://localhost:5000/api/historical-prices')
    print(f'Historical Prices: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'Success: {data["success"]}, Records: {len(data["data"])}')
except Exception as e:
    print(f'Historical prices check failed: {e}')

print('=== Test Complete ===')