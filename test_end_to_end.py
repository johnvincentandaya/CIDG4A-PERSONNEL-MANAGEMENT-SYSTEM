import requests
import json

print("=== COMPLETE END-TO-END TEST ===\n")

BASE_URL = 'http://127.0.0.1:8001'
FRONTEND_ORIGIN = 'http://localhost:3000'

tests = [
    {
        'name': 'Basic Personnel Creation',
        'method': 'POST',
        'endpoint': '/api/personnel/basic',
        'data': {
            'rank': 'PCOL',
            'last_name': 'ANGELES',
            'first_name': 'RAMON',
            'unit': 'BATANGAS',
            'status': 'ACTIVE',
            'birthdate': '1985-06-15',
            'religion': 'CATHOLIC',
        }
    },
    {
        'name': 'NUP Personnel Creation',
        'method': 'POST',
        'endpoint': '/api/personnel/basic',
        'data': {
            'rank': 'NUP',
            'nup_rank': 'MAJOR',
            'nup_entry_number': '12345',
            'last_name': 'SANTOS',
            'first_name': 'MARIA',
            'unit': 'RHQ',
            'status': 'ACTIVE',
            'birthdate': '1992-03-20',
            'religion': 'PROTESTANT',
            'section': 'OPERATIONS',
        }
    },
    {
        'name': 'Fetch Personnel List',
        'method': 'GET',
        'endpoint': '/api/personnel/',
        'data': {}
    }
]

for test in tests:
    print(f"Test: {test['name']}")
    print(f"  {test['method']} {test['endpoint']}")
    
    try:
        if test['method'] == 'POST':
            files = {k: (None, v) for k, v in test['data'].items()}
            resp = requests.post(
                f"{BASE_URL}{test['endpoint']}",
                files=files,
                headers={'Origin': FRONTEND_ORIGIN},
                timeout=5
            )
        else:
            resp = requests.get(
                f"{BASE_URL}{test['endpoint']}",
                headers={'Origin': FRONTEND_ORIGIN},
                timeout=5
            )
        
        cors_header = resp.headers.get('access-control-allow-origin', 'MISSING')
        status_icon = '✓' if resp.status_code in [200, 201] else '✗'
        
        print(f"  Status: {status_icon} {resp.status_code}")
        print(f"  CORS: {cors_header}")
        
        if resp.status_code in [200, 201]:
            if test['method'] == 'POST' and test['endpoint'] == '/api/personnel/basic':
                data = resp.json()
                print(f"  Created: ID={data.get('id')}, Name={data.get('first_name')} {data.get('last_name')}")
        
    except Exception as e:
        print(f"  Status: ✗ ERROR: {str(e)}")
    
    print()

print("=== END-TO-END TEST COMPLETE ===")
print("\nYou can now test the frontend Form 201 component!")
