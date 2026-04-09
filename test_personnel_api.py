import requests
import json
from datetime import datetime

# Test POST to /api/personnel/basic
url = 'http://127.0.0.1:8001/api/personnel/basic'

data = {
    'rank': 'PGEN',
    'last_name': 'TEST',
    'first_name': 'USER',
    'unit': 'RHQ',
    'status': 'ACTIVE',
    'birthdate': '1990-01-01',
    'religion': 'CATHOLIC',
}

files = {k: (None, v) for k, v in data.items()}

print("Testing POST /api/personnel/basic")
print(f"Payload: {data}\n")

try:
    resp = requests.post(url, files=files, timeout=5)
    print(f"Status: {resp.status_code}")
    print(f"Response:\n{json.dumps(resp.json(), indent=2)}")
    
    # Check CORS headers
    print(f"\nCORS Headers:")
    for k, v in resp.headers.items():
        if 'access-control' in k.lower():
            print(f"  {k}: {v}")
            
except Exception as e:
    print(f"Error: {str(e)}")
