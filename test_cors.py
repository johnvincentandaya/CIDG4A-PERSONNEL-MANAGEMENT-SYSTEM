import requests

endpoints = [
    'http://127.0.0.1:8001/',
    'http://127.0.0.1:8001/api/bmi',
    'http://127.0.0.1:8001/api/personnel',
]

print("Testing CORS configuration...\n")

for url in endpoints:
    try:
        resp = requests.get(url, headers={'Origin': 'http://localhost:3000'}, timeout=2)
        cors_header = resp.headers.get('access-control-allow-origin', 'MISSING')
        creds_header = resp.headers.get('access-control-allow-credentials', 'not-set')
        print(f"GET {url}")
        print(f"  Status: {resp.status_code}")
        print(f"  access-control-allow-origin: {cors_header}")
        print(f"  access-control-allow-credentials: {creds_header}")
        print()
    except Exception as e:
        print(f"GET {url}: ERROR - {str(e)}\n")

print("CORS is properly configured!" if all(
    'localhost:3000' in requests.get(url, headers={'Origin': 'http://localhost:3000'}, timeout=2).headers.get('access-control-allow-origin', '')
    for url in endpoints
) else "CORS configuration needs review")
