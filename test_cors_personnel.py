import requests
import json

url = 'http://127.0.0.1:8001/api/personnel/basic'
data = {
    'rank': 'PGEN',
    'last_name': 'TEST2',
    'first_name': 'USER2',
    'unit': 'RHQ',
    'status': 'ACTIVE',
    'birthdate': '1990-05-01',
    'religion': 'CATHOLIC',
}

files = {k: (None, v) for k, v in data.items()}

# Make request with CORS header
resp = requests.post(url, files=files, headers={'Origin': 'http://localhost:3000'})

print(f'Status: {resp.status_code}')
print(f'\nCORS Headers:')
cors_found = False
for k, v in resp.headers.items():
    if 'access-control' in k.lower():
        cors_found = True
        print(f'  ✓ {k}: {v}')

if not cors_found:
    print("  No CORS headers found")

if resp.status_code == 200:
    data = resp.json()
    print(f'\n✓ Personnel record created successfully!')
    print(f'  ID: {data["id"]}')
    print(f'  Name: {data["first_name"]} {data["last_name"]}')
    print(f'  Department: {data["unit"]}')
