import requests
import json

url = 'http://127.0.0.1:8001/api/personnel/report'

data = {
    'file_name': 'test_report',
    'report_type': 'excel',
    'scope': 'Overall'
}

files = {k: (None, v) for k, v in data.items()}

print("Testing POST /api/personnel/report")
print(f"Payload: {data}\n")

try:
    resp = requests.post(url, files=files, headers={'Origin': 'http://localhost:3000'}, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response Length: {len(resp.content)} bytes")
    
    # Check if it's JSON or binary
    try:
        print(f"Response (JSON):\n{json.dumps(resp.json(), indent=2)}")
    except:
        print(f"Response (Text):\n{resp.text[:500]}")
    
    # Check CORS headers
    print(f"\nCORS Headers:")
    cors_found = False
    for k, v in resp.headers.items():
        if 'access-control' in k.lower():
            cors_found = True
            print(f"  {k}: {v}")
    
    if not cors_found:
        print("  No CORS headers found")
        
except Exception as e:
    print(f"Error: {str(e)}")
